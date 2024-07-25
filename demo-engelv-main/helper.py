# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models
import os
import streamlit as st
import googlemaps
import re
from secrets_env import GMAPS_API_KEY
import logging


gmaps = googlemaps.Client("AIzaSyCuAp0PDC2m4MKQX8AR70c_e7rnCgdpsIc")

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "key-app-engelv.json"

def generate(prompt, vision=False):
   vertexai.init(project="hooli-420412", location="europe-west3")

   if vision:
      model = GenerativeModel("gemini-1.0-pro-vision-001")
   else:
      model = GenerativeModel("gemini-1.0-pro-001")
   
   responses = model.generate_content(
      prompt,
      generation_config={
         "max_output_tokens": 2048,
         "temperature": 0.4,
         "top_p": 1
         },
         safety_settings={
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }, 
            stream=False)
   
   print("GENERATE")
   print(responses.text)
   
   return responses.text


def extract_names(content_json):
  prompt_extract_names = f"""
  Give me all values from the name, lat and lng. 
  Put them in a list of dictionaries. Convert Umlauts.
  Output only dictionary
  
  Input: {content_json}
  """
  print("EXTRACT NAMES")
  response = generate(prompt_extract_names)
  print(response)

  response = re.findall(r"\[{1}[^\]]+\]", response)[0]
  print("RE ----------------")
  print(response)
  print("--------------")

  return response

@st.cache_data
def get_places(type: str, lat: str, lng: str, radius=1000):

    places = gmaps.places_nearby(radius=radius, location=f"{lat},{lng}", type=type)
    print("places received")
    logging.info(places)
    places_extracted = extract_names(places)
    logging.info(places_extracted)
    places_extracted = eval_json(places_extracted)
    places_with_distances = eval(places_extracted)


    print("names extracted")
    print(places_extracted)

    distances = gmaps.distance_matrix(origins=f"{lat},{lng}", destinations=places_with_distances, mode="walking")

    for idx, distance in enumerate(distances.get("rows")[0].get("elements")):
       places_with_distances[idx]
       places_with_distances[idx]["Gehweg in Minuten"] = distance.get("duration").get("text")

    print("GET PLACES")
    print(places_with_distances)
    
    return places_with_distances

def generate_location_desc(prompt: str):
   print("GENERATE LOCATION DESC")
   print("prompt")
   return generate(prompt)

def extract_details_from_groundplan(groundplan: bytes):
    groundplan = Part.from_data(data=groundplan, mime_type="image/jpeg")

    groundplan1 = open("media/Grundriss1.jpeg", "br").read()
    groundplan1 = Part.from_data(data=groundplan1, mime_type="image/jpeg")

    groundplan2 = open("media/Grundriss2.jpg", "br").read()
    groundplan2 = Part.from_data(data=groundplan2, mime_type="image/jpeg")

    prompt = ["""Du bist ein Experte für Immobilien
              Die Küche, die Garage, HWR, Flur, Garderrobe und das Badezimmer zählen nicht als Zimmer
              Loggia wird mit einem Balkon gleichgesetzt""", 
              groundplan1, 
              """{\"Anzahl_zimmer\": 3, \"Wohnzimmer\": 
              \"ja\", \"Schlafzimmer\":\"ja\", \"Kinderzimmer\":\"ja\", \"Badezimmer\":\"ja\", \"Küche\":\"ja\", 
              \"Garage\":\"nein\", \"Balkon\":\"ja\", \"Arbeitszimmer\":\"nein\"}""",
              groundplan2, """{\"Anzahl_zimmer\": 3, 
              \"Wohnzimmer\": \"ja\", \"Schlafzimmer\":\"ja\", \"Kinderzimmer\":\"ja\", \"Badezimmer\":\"ja\", \"Küche\":\"ja\", 
              \"Garage\":\"ja\", \"Balkon\":\"nein\", \"Arbeitszimmer\":\"ja\"}""",
              groundplan]
    
    return eval(generate(prompt, vision=True))

def get_coordinates_for_address(address: str):
    print("GET COORDINATES")
    geocode = gmaps.geocode(st.session_state.address)[0].get("geometry").get("location")
    lat = geocode.get("lat")
    lng = geocode.get("lng")

    return lat, lng

def eval_json(data: str):
   return re.findall(r"\[{1}[^\]]+\]", data)[0]