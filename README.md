# Vtubestudio-Ocarina
A websockets plugin for Vtube studio to create real-time ocarina tracking

# Compiling in python
The script requires websockets, pyaudio, aubio, and numpy. Make sure you install these in your python environment before compiling.

# Live2D Cubism setup
1. Create a new parameter. Recommend calling it "OcarinaNote" but the name doesn't matter as long as it's clear and can be found in VTube Studio
2. Set 12 keyframes roughly evenly spaced.
3. The 0 keyframe will be the idle pose where the instrument isn't being played
4. In ascending order from the 0.08 keyframe onward, each is one note on the ocarina, from the low C4 up to the F5 note. Reference for accurate ocarina fingering can be found in this video: https://www.youtube.com/watch?v=L9-qLMfZ7B0
  Text reference for ocarina fingerings
     0.08	C4	All 10 main holes covered
     0.17	D4	Right Pinky lifted
     0.25	E4	Right Ring lifted
     0.33	F4	Right Middle lifted
     0.42	G4	Right Index lifted
     0.50	A4	Left Ring lifted (On the left hand, the pinky is NOT lifted first)
     0.58	B4	Left Middle lifted
     0.67	C5	Left Index lifted
     0.75	D5	Left Pinky lifted
     0.83	E5	Right Thumb lifted
     0.92	F5	Left Thumb lifted (All open)
5. The 1.0 keyframe is a high note with all holes uncovered.

# Vtube Studio Setup
1. In the General settings, ensure that Vtube Studio Plugins "Start API" toggle is enabled. Make sure the port is the same as in the config file.
2. Run the compiled script and make sure it connects to the VTS API
3. In the Model settings, create a new model control.
   3a. Set the "Input" to "ParamOcarinaNote" (or whatever you have the custom parameter name set as in the config file). If this option isn't showing up, it's because the plugin isn't sending any data to VTS to create the custom input parameter. 
   3b. Set the "Output" to "OcarinaNote" (or whatever you named the parameter in Cubism)

   
# config.json
vts_websocket_uri: the address to your vtube studio websockets API. default is "ws://localhost:8001"  
min_frequency: the low frequency of the ocarina (when all holes are covered), default is 550  
max_frequency: the high frequency of the ocarina (when all holes are uncovered), default is 1310  
confidence_threshold: How close the frequency should be before snapping to a certain keyframe, default 0.8  
parameter_name": The vtubestudio parameter name, change this if for some reason you have a conflicting parameter, default is "ParamOcarinaNote"
