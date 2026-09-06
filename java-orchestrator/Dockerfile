FROM eclipse-temurin:21-jre-jammy

WORKDIR /app

# Copy pre-compiled Spring Boot executable fat JAR
COPY target/java-orchestrator-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]
