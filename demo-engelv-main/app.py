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


import streamlit as st
import googlemaps
from helper import get_places, generate_location_desc, extract_details_from_groundplan, get_coordinates_for_address
from secrets_env import GMAPS_API_KEY
from vertexai.preview.generative_models import Part
from helper import generate
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

gmaps = googlemaps.Client("AIzaSyCuAp0PDC2m4MKQX8AR70c_e7rnCgdpsIc")

st.sidebar.image("media/logo-vonovia.png")
st.sidebar.subheader("Automatisierte Generierung von Immobilien-Exposés")
st.sidebar.text_input("Adresse der Immobilie", key="address")

lat, lng = None, None

column_config = {
    "name": "Name",
    "lat": "Breitengrad",
    "lng": "Längengrad"
    }

if st.session_state.address:
    st.header("1) Details aus Google Maps", divider="rainbow")
    st.subheader(":station: Haltestellen")
    lat, lng = get_coordinates_for_address(st.session_state.address)

    print(f"Received lat, lng: {lat}, {lng}")

    bus_station = get_places("bus_station", lat, lng)
    print("subway stations retrieved")
    st.dataframe(bus_station, height=200, use_container_width=True, hide_index=True, column_config=column_config)

    st.subheader(":bread: Bäckereien")
    bakeries = get_places("bakery", lat, lng, radius=700)
    print("bakeries retrieved")
    st.dataframe(bakeries, height=200, use_container_width=True, hide_index=True, column_config=column_config)

    st.subheader(":office: Stadt-Zentrum")
    city_hall = get_places("city_hall", lat, lng, radius=1500)
    st.dataframe(city_hall, use_container_width=True, hide_index=True, column_config=column_config)
    
    st.header("2) Lagebeschreibung für das Exposé via Gemini", divider="rainbow")

    prompt = f"""
    Schreibe einen Text für die Lage eines Immobilieninserats für eine Wohnung
    Du bist ein Immobilien-Experte
    Schreibe positiv und begeistere Kunden
    Schreibe eine griffige Überschrift mit Bezug auf die Lage der Immobilie
    Liste 2 bis 3 Beispiele zu öffentlichen Verkehrsmitteln und Bäckereien
    Nutze valides Markdown

    Öffentliche Verkehrsmittel:
    {bus_station}

    Bäckereien:
    {bakeries}

    Entfernung zum Stadt-Zentrum:
    {city_hall}
    """

    prompt_override = st.text_area("Prompt für das LLM", value=prompt, height=500)

    if prompt_override:
        prompt = prompt_override

    if st.button("Generiere den Text", type="primary", key="button_generate"):
        st.write(generate_location_desc(prompt))
        st.session_state.clicked = False
    
    st.header("2) Extrahieren der Basis-Daten aus dem Grundriss", divider="rainbow")

    groundplan = st.file_uploader("Grundriss hochladen")
    if not groundplan:
        button_disabled = True
    
    if groundplan:
        st.image(groundplan.getvalue())
        button_disabled = False
    
    if st.button("Extrahiere Basis-Daten", type="primary", key="button_extract_from_groundplan", disabled=button_disabled):
        st.dataframe(extract_details_from_groundplan(groundplan.getvalue()), use_container_width=True, column_config={
            "value": "Wert"
        })
        st.session_state.clicked = False




