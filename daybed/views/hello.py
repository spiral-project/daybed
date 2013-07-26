from cornice import Service

from daybed import VERSION

hello = Service(name="hello",
                path='/',
                description="Welcome",
                renderer="jsonp")


@hello.get()
def get_hello(request):
    return {'daybed': 'hello', 'version': VERSION}
