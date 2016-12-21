import falcon
import service


app = falcon.API()
services = service.Services()
service_instance = service.Service()
service_action_handler = service.ServiceAction()

app.add_route('/services', services)
app.add_route('/services/{id}', service_instance)
app.add_route('/services/{id}/{action}', service_action_handler)
