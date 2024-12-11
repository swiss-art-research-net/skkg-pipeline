import gr.forth.ics.isl.x3ml.X3MLEngineFactory;
import gr.forth.ics.isl.x3ml.X3MLEngine;
import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.lang.reflect.Field;


public class X3MLEngineService {

    private static X3MLEngineFactory engineFactory;
    // Initialize X3MLEngineFactory once as a singleton
    public static synchronized void initializeX3MLEngine() {
        if (engineFactory == null) {
            engineFactory = X3MLEngineFactory.create();
            System.out.println("X3MLEngineFactory instance created");
        }
    }

    public static void main(String[] args) throws IOException {
        initializeX3MLEngine();
        // HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", 8089), 0); // Bind to all interfaces
        server.createContext("/transform", new TransformHandler());
        server.setExecutor(null);
        server.start();
        System.out.println("Server is listening on port 8089");
    }

    static class TransformHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if ("POST".equals(exchange.getRequestMethod())) {
                Map<String, String> params = queryToMap(exchange.getRequestURI().getQuery());

                try {
                    File mappingFile = new File(params.get("mappingFile"));
                    File inputFile = new File(params.get("inputFile"));
                    File generatorPolicy = new File(params.get("generatorPolicy"));
                    File outputFile = new File(params.get("outputFile"));

                    configureAndExecute(mappingFile, inputFile, generatorPolicy, outputFile);

                    String response = "Transformation completed successfully. Output: " + outputFile.getAbsolutePath();
                    exchange.sendResponseHeaders(200, response.length());
                    try (OutputStream os = exchange.getResponseBody()) {
                        os.write(response.getBytes());
                    }
                } catch (Exception e) {
                    String response = "Error during transformation: " + e.getMessage();
                    exchange.sendResponseHeaders(500, response.length());
                    try (OutputStream os = exchange.getResponseBody()) {
                        os.write(response.getBytes());
                    }
                    e.printStackTrace();
                }                
            } else {
                exchange.sendResponseHeaders(405, -1);
            }
        }
    }

    private static void configureAndExecute(File mappingFile, File inputFile, File generatorPolicy, File outputFile) throws Exception {
        try {
            System.out.println("Starting X3ML processing");
            // new instance
            X3MLEngineFactory factory = X3MLEngineFactory.create();

            factory.withInputFiles(inputFile);
            factory.withMappings(mappingFile);
            
            factory.withGeneratorPolicy(generatorPolicy);
            factory.withOutput(outputFile, X3MLEngineFactory.OutputFormat.TURTLE);
            
            factory.execute();
        } catch (Exception e) {
            System.out.println("X3ML processing failed at stage: " + e.getClass().getName());
            throw e;
        }
    }

    private static Map<String, String> queryToMap(String query) {
        Map<String, String> result = new HashMap<>();
        for (String param : query.split("&")) {
            String[] entry = param.split("=");
            if (entry.length > 1) {
                result.put(entry[0], entry[1]);
            }
        }
        return result;
    }
}
