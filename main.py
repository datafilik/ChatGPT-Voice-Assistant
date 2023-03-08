import openai
import pyttsx3 as tts
import speech_recognition as sr
from pygame import mixer
import time

from py_error_handler import noalsaerr # to suppress ALSA lib dumps

import os

from dotenv import load_dotenv
load_dotenv() # load environment variable from .env file

# get OpenAI API key
openai.api_key =  os.environ['OPENAI_API_KEY'] # os.getenv("OPENAI_API_KEY")

# text-to-speech engine instance
tts_engine = tts.init()
# voices = tts_engine.getProperty('voices')
# tts_engine.setProperty('voice', voices[-1].id)

# functions for transcribing sound from file to text
def sr_transcribe_audio_to_text(file_name):
  recognizer = sr.Recognizer()
  with sr.AudioFile(file_name) as source:
    audio_data = recognizer.record(source)
  try:
    return recognizer.recognize_google(audio_data)
  except:
    print("Ah, let's give this another try.")


def whisper_transcribe_audio_to_text(file_name):
  audio_data= open(file_name, "rb")
  try:
    transcript = openai.Audio.transcribe("whisper-1", audio_data)
    return transcript["text"]
  except:
    print("Ah, let's give this another try.")

# functions using OpenAI API to generate reponse to user query
def generate_prompt_response(prompt):
  response = openai.Completion.create(engine="text-davinci-003",
                                      prompt=prompt,
                                      max_tokens=4000,
                                      n=1,
                                      stop=None,
                                      temperature=0.5)
  return response["choices"][0]["text"]


def generate_chat_response(msg):
  response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
          {"role": "user", "content": msg}
      ]
  )
  return response.choices[0].message["content"]
  # return response["choices"][0]["message"]["content"]

# transcribe text string to sound
def speak(text):
  tts_engine.say(text)
  tts_engine.runAndWait()


def play_sound_file(sound_file):
  # input - sound_file specifies path to sound file in string
  mixer.init()
  mixer.music.load(sound_file)
  mixer.music.play()
  # mixer.music.stop()

# main
def main(gpt_version): 
  # Input - gpt_version takes valid values of 'gpt-3' and 'gpt-3.5'

  no_activity_period_count = 0 # for ending convo session automatically

  while True:
    # TODO find and fix cause of the ALSA dumps
    with noalsaerr():  # suppress ALSA lib dumps for now. remove when dump issues are fixed
      recognizer = sr.Recognizer()
      # initial prompt ('Hey! Kai' in this case) to begin recording
      print("Say 'Hey Kai' to record your question...")
      
      with sr.Microphone() as source:
        source.pause_threshold = 1
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

        try:
          transcription = recognizer.recognize_google(audio)
          #if transcription.lower == "lex":

          print("Yes. How may I be of help?")
          speak("Yes. How may I be of help?")

          # record audio
          in_audio_filename = "input.wav"

          with sr.Microphone() as source:
            source.pause_threshold = 1
            recognizer.adjust_for_ambient_noise(source)
            
            audio = recognizer.listen(source,
                                      phrase_time_limit=None,
                                      timeout=None)  

            with open(in_audio_filename, "wb") as f:
              f.write(audio.get_wav_data())

          # transcribe audio to text
          # text = sr_transcribe_audio_to_text(in_audio_filename)
          text = whisper_transcribe_audio_to_text(in_audio_filename)
          if text:
            print("You said: '{}'.".format(text))
            speak("You asked, '{}'.".format(text))

            # generate response
            if gpt_version == "gpt-3":
              response = generate_prompt_response(text)
            elif gpt_version == "gpt-3.5":
              response = generate_chat_response(text)

            print("GPT response: {}".format(response))

            #read out response
            speak(response)
            speak("I hope that helped. You can ask your next question.")
            # reset counter
            no_activity_period_count = 0 

        except sr.RequestError: 
          print("API unavailable")

        except sr.UnknownValueError:
          print("Unable to recognize speech")
          # speak("I could not hear you.") 
          # play a brief sound file for non active period
          play_sound_file("ambient-music-0036.mp3")
          
          #print(no_activity_period_count)
          no_activity_period_count += 1

    # Temporal way to end question and answer loop due to non activity
    # stops session after 3 instance of no prompts
    if no_activity_period_count > 3:
      time.sleep(2)
      speak("Bye for now.")
      break



        # except sr.RequestError:  # Exception as e:
        #   print("An error occured: {}".format(e))
    # TODO create way to end question and answer loop smoothly


if __name__ == "__main__":
  main("gpt-3.5") # change parameter to gpt-3.5 to use the latest gpt-3.5-turbo model
