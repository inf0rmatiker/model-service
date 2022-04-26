import http.client

conn = http.client.HTTPSConnection("ant.cs.colostate.edu", 5000)
payload = "{\n  \"label_field\": \"SOIL_TEMPERATURE_0_TO_01_M_BELOW_SURFACE_KELVIN\",\n  \"feature_fields\": [\n    \"PRESSURE_REDUCED_TO_MSL_PASCAL\",\n    \"VISIBILITY_AT_SURFACE_METERS\",\n    \"VISIBILITY_AT_CLOUD_TOP_METERS\",\n    \"WIND_GUST_SPEED_AT_SURFACE_METERS_PER_SEC\",\n    \"PRESSURE_AT_SURFACE_PASCAL\",\n    \"TEMPERATURE_AT_SURFACE_KELVIN\",\n    \"DEWPOINT_TEMPERATURE_2_METERS_ABOVE_SURFACE_KELVIN\",\n    \"RELATIVE_HUMIDITY_2_METERS_ABOVE_SURFACE_PERCENT\",\n    \"ALBEDO_PERCENT\",\n    \"TOTAL_CLOUD_COVER_PERCENT\"\n  ],\n  \"hyper_parameters\": {\n    \"epochs\": 5,\n    \"learning_rate\": 0.001,\n    \"normalize_inputs\": true,\n    \"train_split\": 0.8,\n    \"optimizer_type\": \"ADAM\",\n    \"loss_type\": \"MEAN_SQUARED_ERROR\",\n    \"input_layer\": { \"activation\": \"RELU\", \"name\": \"input_layer_0\" },\n    \"hidden_layers\": [\n      { \"activation\": \"RELU\", \"units\": 32, \"name\": \"hidden_layer_1\" },\n      { \"activation\": \"RELU\", \"units\": 16, \"name\": \"hidden_layer_2\" }\n    ],\n    \"output_layer\": { \"activation\": \"RELU\", \"name\": \"output_layer_3\" }\n  }\n}"
headers = {
  'Content-Type': 'application/json'
}
conn.request("POST", "/model", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))