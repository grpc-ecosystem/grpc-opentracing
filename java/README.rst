#####################
GRPC-Java OpenTracing
#####################

============
Installation
============

This package is available on Maven Central and can be added to your project as follows:

**Maven**
```
<dependencies>
	<dependency>
		<groupId>io.opentracing.contrib.grpc</groupId>
		<artifactId>grpc-opentracing</artifactId>
		<version>0.1.0</version>
	</dependency>
</dependencies>
```

**Gradle**
```
compile 'io.opentracing.contrib.grpc:grpc-opentracing:0.1.0'
```

**Note:** This package was developed using grpc-java v1.0.0-pre1.

==========
QuickStart
========== 

If you want to add basic tracing to your clients and servers, you can do so in a few short and simple steps. (These code snippets use the grpc example's generated GreeterGrpc.java)

**Clients**

- Instantiate a tracer
- Create a `ClientTracingInterceptor`
- Intercept the client channel

	```java
	public class YourClient {

		private final ManagedChannel channel;
  		private final GreeterGrpc.GreeterBlockingStub blockingStub;

		public YourClient(String host, int port) {
			channel = ManagedChannelBuilder.forAddress(host, port)
				.usePlaintext(true)
				.build();
		
			Tracer tracer = yourOpenTracingTracer; # any implementation of io.opentracing.Tracer
			ClientTracingInterceptor tracingInterceptor = new ClientTracingInterceptor(tracer)

			blockingStub = GreeterGrpc.newBlockingStub(tracingInterceptor.intercept(channel));
		}
	}
	```
**Servers**

- Instantiate a tracer
- Create a `ServerTracingInterceptor`
- Intercept a service 
	
	```java
	public class YourServer {

		private int port;
	  	private Server server;

	  	private void start() throws IOException {
		
			Tracer tracer = yourOpenTracingTracer;
			ServerTracingInterceptor tracingInterceptor = new ServerTracingInterceptor(tracer);

			server = ServerBuilder.forPort(port)
				.addService(tracingInterceptor.intercept(someServiceDef))
				.build()
				.start();

			Runtime.getRuntime().addShutdownHook(new Thread() {
			  	@Override
			  	public void run() {
					HelloWorldServer.this.stop();
				}
			});
		}
	}
	```

==============
Server Tracing
==============

==============
Client Tracing
==============




