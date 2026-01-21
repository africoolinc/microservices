from flask import Flask
import consul
import os

app = Flask(__name__)
service_id = os.environ.get('SERVICE_ID', 'unknown')
c = consul.Consul(host='consul', port=8500)

# Register service with Consul
c.agent.service.register(
    name=service_id,
    service_id=service_id,
    address=service_id,
    port=5000,
    check=consul.Check.http(url='http://localhost:5000/health', interval='10s')
)

@app.route('/')
def hello():
    return f'Hello from {service_id}'

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
