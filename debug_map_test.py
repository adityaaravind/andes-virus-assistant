#!/usr/bin/env python3
"""Debug script to test basic map functionality."""

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Map Debug Test", layout="wide")
st.title("🗺️ Map Debug Test")

# Test 1: Basic HTML component
st.subheader("Test 1: Basic HTML Component")
test_html = """
<div style="width: 100%; height: 200px; background: red; color: white; display: flex; align-items: center; justify-content: center; font-size: 20px;">
    BASIC HTML TEST - RED BACKGROUND
</div>
"""
components.html(test_html, height=200)

# Test 2: Simple Leaflet Map
st.subheader("Test 2: Simple Leaflet Map")
leaflet_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        html, body { margin: 0; padding: 0; height: 100%; }
        #map { width: 100%; height: 100%; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        console.log('Initializing map...');
        try {
            var map = L.map('map').setView([0, 0], 2);
            console.log('Map created');

            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '© CartoDB',
                maxZoom: 18
            }).addTo(map);
            console.log('Tiles added');

            L.marker([0, 0]).addTo(map)
                .bindPopup('Test marker at 0,0')
                .openPopup();
            console.log('Marker added');

        } catch (e) {
            console.error('Map error:', e);
            document.getElementById('map').innerHTML = '<div style="padding: 20px; color: red;">Map Error: ' + e.message + '</div>';
        }
    </script>
</body>
</html>
"""
components.html(leaflet_html, height=400)

# Test 3: Map with debugging
st.subheader("Test 3: Map with Debug Console")
debug_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        html, body { margin: 0; padding: 0; height: 100%; font-family: sans-serif; }
        #container { height: 100%; display: flex; flex-direction: column; }
        #map { flex: 1; }
        #debug { background: #333; color: white; padding: 10px; font-size: 12px; max-height: 100px; overflow-y: auto; }
    </style>
</head>
<body>
    <div id="container">
        <div id="map"></div>
        <div id="debug">Debug console...<br></div>
    </div>
    <script>
        function log(msg) {
            document.getElementById('debug').innerHTML += new Date().toLocaleTimeString() + ': ' + msg + '<br>';
        }

        log('Starting map initialization...');

        try {
            log('Checking if Leaflet is loaded: ' + (typeof L !== 'undefined'));

            var map = L.map('map').setView([20, 0], 2);
            log('Map created successfully');

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            log('Tiles added successfully');

            // Add a test marker
            L.marker([20, 0]).addTo(map)
                .bindPopup('Test marker')
                .openPopup();
            log('Marker added successfully');

            log('Map fully initialized!');

        } catch (e) {
            log('ERROR: ' + e.message);
            console.error(e);
        }
    </script>
</body>
</html>
"""
components.html(debug_html, height=500)