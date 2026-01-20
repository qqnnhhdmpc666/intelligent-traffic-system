import javax.swing.*;
import java.awt.*;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class TrafficClient extends JFrame {
    private JTextField startNodeField;
    private JTextField endNodeField;
    private JComboBox<String> vehicleTypeComboBox;
    private JTextArea resultArea;

    public TrafficClient() {
        setTitle("Intelligent Traffic System - Path Planning Client");
        setSize(600, 400);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout());

        // Input Panel
        JPanel inputPanel = new JPanel(new GridLayout(4, 2, 10, 10));
        inputPanel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));
        
        inputPanel.add(new JLabel("Start Node:"));
        startNodeField = new JTextField();
        inputPanel.add(startNodeField);
        
        inputPanel.add(new JLabel("End Node:"));
        endNodeField = new JTextField();
        inputPanel.add(endNodeField);
        
        inputPanel.add(new JLabel("Vehicle Type:"));
        vehicleTypeComboBox = new JComboBox<>(new String[]{"normal", "emergency"});
        inputPanel.add(vehicleTypeComboBox);
        
        JButton requestButton = new JButton("Request Path");
        requestButton.addActionListener(e -> requestPath());
        inputPanel.add(new JLabel()); // Placeholder
        inputPanel.add(requestButton);

        // Result Panel
        resultArea = new JTextArea();
        resultArea.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(resultArea);
        scrollPane.setBorder(BorderFactory.createTitledBorder("Path Planning Result"));

        add(inputPanel, BorderLayout.NORTH);
        add(scrollPane, BorderLayout.CENTER);
    }

    private void requestPath() {
        String startNode = startNodeField.getText().trim();
        String endNode = endNodeField.getText().trim();
        String vehicleType = (String) vehicleTypeComboBox.getSelectedItem();

        if (startNode.isEmpty() || endNode.isEmpty()) {
            resultArea.setText("Please input start and end nodes");
            return;
        }

        resultArea.setText("Requesting path...");

        // Asynchronous request to avoid UI blocking
        new Thread(() -> {
            try {
                // Create HTTP connection
                URL url = new URL("http://localhost:8000/api/request_path");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);

                // Build JSON request body
                String jsonInputString = String.format(
                        "{\"start_node\": \"%s\", \"end_node\": \"%s\", \"vehicle_type\": \"%s\"}",
                        startNode, endNode, vehicleType
                );

                // Send request
                try (OutputStream os = conn.getOutputStream()) {
                    byte[] input = jsonInputString.getBytes("utf-8");
                    os.write(input, 0, input.length);
                }

                // Read response
                int responseCode = conn.getResponseCode();
                if (responseCode == HttpURLConnection.HTTP_OK) {
                    BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                    String inputLine;
                    StringBuilder response = new StringBuilder();

                    while ((inputLine = in.readLine()) != null) {
                        response.append(inputLine);
                    }
                    in.close();

                    // Parse JSON response
                    String responseString = response.toString();
                    // Simple parsing to extract path and time
                    String path = extractPath(responseString);
                    String duration = extractDuration(responseString);
                    String message = extractMessage(responseString);

                    final String resultText = String.format(
                            "Request successful!\n" +
                            "Path: %s\n" +
                            "Estimated time: %s seconds\n" +
                            "Message: %s",
                            path, duration, message
                    );

                    // Update UI (must be in EDT thread)
                    SwingUtilities.invokeLater(() -> {
                        resultArea.setText(resultText);
                    });
                } else {
                    final String errorText = "Request failed, status code: " + responseCode;
                    SwingUtilities.invokeLater(() -> {
                        resultArea.setText(errorText);
                    });
                }
            } catch (Exception e) {
                final String errorText = "Request exception: " + e.getMessage();
                SwingUtilities.invokeLater(() -> {
                    resultArea.setText(errorText);
                });
            }
        }).start();
    }

    // Simple JSON parsing method (avoid additional dependencies)
    private String extractPath(String json) {
        int pathStart = json.indexOf("\"path\":[");
        int pathEnd = json.indexOf("]", pathStart);
        if (pathStart != -1 && pathEnd != -1) {
            return json.substring(pathStart + 8, pathEnd).replace("\"", "").replace(",", " -> ");
        }
        return "Unknown";
    }

    private String extractDuration(String json) {
        int durationStart = json.indexOf("\"duration\":");
        if (durationStart != -1) {
            int commaIndex = json.indexOf(",", durationStart);
            if (commaIndex != -1) {
                return json.substring(durationStart + 11, commaIndex).trim();
            }
        }
        return "0";
    }

    private String extractMessage(String json) {
        int messageStart = json.indexOf("\"message\":\"");
        int messageEnd = json.indexOf("\"", messageStart + 10);
        if (messageStart != -1 && messageEnd != -1) {
            return json.substring(messageStart + 10, messageEnd);
        }
        return "None";
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            TrafficClient client = new TrafficClient();
            client.setVisible(true);
        });
    }
}
