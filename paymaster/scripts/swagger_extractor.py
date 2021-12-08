openapi_data = app.openapi()
with open('schema.yml', 'w') as file:
    yaml.dump(openapi_data, file)