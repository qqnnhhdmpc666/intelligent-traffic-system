import javax.swing.*;
import java.awt.*;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;

public class TrafficClient extends JFrame {
    private JTextField startNodeField;
    private JTextField endNodeField;
    private JComboBox<String> vehicleTypeComboBox;
    private JTextArea resultArea;
    private JTextArea infoArea;
    private JTextArea nodesRoadsArea;
    private JTextArea statsArea;
    private JTabbedPane tabbedPane;
    
    // Store nodes list
    private List<String> nodesList = new ArrayList<>();
    // Store roads list
    private List<String> roadsList = new ArrayList<>();

    public TrafficClient() {
        setTitle("Intelligent Traffic System - Path Planning Client");
        setSize(900, 700);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout());
        setLocationRelativeTo(null); // Center the window

        // Set look and feel to system default for better appearance
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
            e.printStackTrace();
        }

        // Create tabbed pane with custom colors
        tabbedPane = new JTabbedPane();
        tabbedPane.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        
        // Add path planning tab
        tabbedPane.addTab("Path Planning", createPathPlanningPanel());
        
        // Add system info tab
        tabbedPane.addTab("System Info", createSystemInfoPanel());
        
        // Add nodes and roads tab
        tabbedPane.addTab("Nodes & Roads", createNodesRoadsPanel());
        
        // Add system stats tab
        tabbedPane.addTab("System Stats", createSystemStatsPanel());

        // Add header panel
        JPanel headerPanel = new JPanel();
        headerPanel.setBackground(new Color(44, 62, 80));
        headerPanel.setPreferredSize(new Dimension(getWidth(), 60));
        headerPanel.setLayout(new FlowLayout(FlowLayout.LEFT, 20, 15));
        
        JLabel headerLabel = new JLabel("Intelligent Traffic System");
        headerLabel.setForeground(Color.WHITE);
        headerLabel.setFont(new Font("Segoe UI", Font.BOLD, 20));
        headerPanel.add(headerLabel);

        // Add footer panel
        JPanel footerPanel = new JPanel();
        footerPanel.setBackground(new Color(52, 73, 94));
        footerPanel.setPreferredSize(new Dimension(getWidth(), 40));
        footerPanel.setLayout(new FlowLayout(FlowLayout.CENTER));
        
        JLabel footerLabel = new JLabel("© 2026 Intelligent Traffic System - All Rights Reserved");
        footerLabel.setForeground(Color.LIGHT_GRAY);
        footerLabel.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        footerPanel.add(footerLabel);

        add(headerPanel, BorderLayout.NORTH);
        add(tabbedPane, BorderLayout.CENTER);
        add(footerPanel, BorderLayout.SOUTH);
    }
    
    // Create path planning panel
    private JPanel createPathPlanningPanel() {
        JPanel panel = new JPanel(new BorderLayout(15, 15));
        panel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));
        
        // Input Panel with better design
        JPanel inputPanel = new JPanel();
        inputPanel.setLayout(new GridBagLayout());
        inputPanel.setBackground(new Color(255, 255, 255));
        inputPanel.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(220, 220, 220), 1),
            BorderFactory.createEmptyBorder(20, 20, 20, 20)
        ));
        
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(12, 10, 12, 10);
        gbc.anchor = GridBagConstraints.WEST;
        
        // Start Node
        gbc.gridx = 0;
        gbc.gridy = 0;
        JLabel startNodeLabel = new JLabel("Start Node:");
        startNodeLabel.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        startNodeLabel.setForeground(new Color(51, 51, 51));
        inputPanel.add(startNodeLabel, gbc);
        
        gbc.gridx = 1;
        gbc.gridy = 0;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.weightx = 1.0;
        startNodeField = new JTextField();
        startNodeField.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        startNodeField.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(200, 200, 200), 1),
            BorderFactory.createEmptyBorder(8, 12, 8, 12)
        ));
        startNodeField.setBackground(new Color(255, 255, 255));
        inputPanel.add(startNodeField, gbc);
        
        // End Node
        gbc.gridx = 0;
        gbc.gridy = 1;
        gbc.fill = GridBagConstraints.NONE;
        gbc.weightx = 0;
        JLabel endNodeLabel = new JLabel("End Node:");
        endNodeLabel.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        endNodeLabel.setForeground(new Color(51, 51, 51));
        inputPanel.add(endNodeLabel, gbc);
        
        gbc.gridx = 1;
        gbc.gridy = 1;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.weightx = 1.0;
        endNodeField = new JTextField();
        endNodeField.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        endNodeField.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(200, 200, 200), 1),
            BorderFactory.createEmptyBorder(8, 12, 8, 12)
        ));
        endNodeField.setBackground(new Color(255, 255, 255));
        inputPanel.add(endNodeField, gbc);
        
        // Vehicle Type
        gbc.gridx = 0;
        gbc.gridy = 2;
        gbc.fill = GridBagConstraints.NONE;
        gbc.weightx = 0;
        JLabel vehicleTypeLabel = new JLabel("Vehicle Type:");
        vehicleTypeLabel.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        vehicleTypeLabel.setForeground(new Color(51, 51, 51));
        inputPanel.add(vehicleTypeLabel, gbc);
        
        gbc.gridx = 1;
        gbc.gridy = 2;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.weightx = 1.0;
        vehicleTypeComboBox = new JComboBox<>(new String[]{"normal", "truck"});
        vehicleTypeComboBox.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        vehicleTypeComboBox.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(200, 200, 200), 1),
            BorderFactory.createEmptyBorder(8, 12, 8, 12)
        ));
        vehicleTypeComboBox.setBackground(new Color(255, 255, 255));
        inputPanel.add(vehicleTypeComboBox, gbc);
        
        // Request Button
        gbc.gridx = 0;
        gbc.gridy = 3;
        gbc.gridwidth = 2;
        gbc.fill = GridBagConstraints.CENTER;
        gbc.weightx = 0;
        JButton requestButton = new JButton("Request Path");
        requestButton.setFont(new Font("Segoe UI", Font.BOLD, 14));
        requestButton.setBackground(new Color(52, 152, 219));
        requestButton.setForeground(Color.BLACK);
        requestButton.setFocusPainted(false);
        requestButton.setPreferredSize(new Dimension(200, 45));
        requestButton.setBorder(BorderFactory.createLineBorder(new Color(41, 128, 185), 1));
        requestButton.addActionListener(e -> requestPath());
        inputPanel.add(requestButton, gbc);

        // Result Panel with better design
        JPanel resultPanel = new JPanel(new BorderLayout());
        resultPanel.setBackground(new Color(255, 255, 255));
        resultPanel.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(220, 220, 220), 1),
            BorderFactory.createEmptyBorder(15, 15, 15, 15)
        ));
        
        resultArea = new JTextArea();
        resultArea.setEditable(false);
        resultArea.setFont(new Font("Consolas", Font.PLAIN, 13));
        resultArea.setLineWrap(false);
        resultArea.setWrapStyleWord(true);
        resultArea.setBackground(new Color(248, 249, 250));
        resultArea.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(220, 220, 220), 1),
            BorderFactory.createEmptyBorder(10, 12, 10, 12)
        ));
        
        JScrollPane scrollPane = new JScrollPane(resultArea);
        scrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED);
        scrollPane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED);
        scrollPane.setBorder(null);
        
        resultPanel.add(scrollPane, BorderLayout.CENTER);

        panel.add(inputPanel, BorderLayout.NORTH);
        panel.add(resultPanel, BorderLayout.CENTER);
        
        return panel;
    }
    
    // Create system info panel
    private JPanel createSystemInfoPanel() {
        JPanel panel = new JPanel(new BorderLayout(15, 15));
        panel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));
        
        // Button Panel with better design
        JPanel buttonPanel = new JPanel();
        buttonPanel.setBackground(new Color(255, 255, 255));
        buttonPanel.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(220, 220, 220), 1),
            BorderFactory.createEmptyBorder(20, 20, 20, 20)
        ));
        buttonPanel.setLayout(new FlowLayout(FlowLayout.CENTER, 30, 20));
        
        JButton getInfoButton = new JButton("Get System Info");
        getInfoButton.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        getInfoButton.setBackground(new Color(46, 204, 113));
        getInfoButton.setForeground(Color.BLACK);
        getInfoButton.setFocusPainted(false);
        getInfoButton.setPreferredSize(new Dimension(160, 45));
        getInfoButton.setBorder(BorderFactory.createLineBorder(new Color(39, 174, 96), 1));
        getInfoButton.addActionListener(e -> {
            infoArea.setText("Getting system info...");
            new Thread(() -> {
                try {
                    String info = getSystemInfo();
                    SwingUtilities.invokeLater(() -> infoArea.setText(info));
                } catch (Exception ex) {
                    SwingUtilities.invokeLater(() -> infoArea.setText("Error: " + ex.getMessage()));
                }
            }).start();
        });
        
        JButton healthCheckButton = new JButton("Health Check");
        healthCheckButton.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        healthCheckButton.setBackground(new Color(241, 196, 15));
        healthCheckButton.setForeground(Color.BLACK);
        healthCheckButton.setFocusPainted(false);
        healthCheckButton.setPreferredSize(new Dimension(160, 45));
        healthCheckButton.setBorder(BorderFactory.createLineBorder(new Color(220, 170, 0), 1));
        healthCheckButton.addActionListener(e -> {
            infoArea.setText("Running health check...");
            new Thread(() -> {
                try {
                    String health = getHealthCheck();
                    SwingUtilities.invokeLater(() -> infoArea.setText(health));
                } catch (Exception ex) {
                    SwingUtilities.invokeLater(() -> infoArea.setText("Error: " + ex.getMessage()));
                }
            }).start();
        });
        
        buttonPanel.add(getInfoButton);
        buttonPanel.add(healthCheckButton);
        
        // Info Area with better design
        JPanel infoPanel = new JPanel(new BorderLayout());
        infoPanel.setBackground(new Color(255, 255, 255));
        infoPanel.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(220, 220, 220), 1),
            BorderFactory.createEmptyBorder(15, 15, 15, 15)
        ));
        
        infoArea = new JTextArea();
        infoArea.setEditable(false);
        infoArea.setFont(new Font("Consolas", Font.PLAIN, 13));
        infoArea.setBackground(new Color(248, 249, 250));
        infoArea.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(220, 220, 220), 1),
            BorderFactory.createEmptyBorder(10, 12, 10, 12)
        ));
        JScrollPane scrollPane = new JScrollPane(infoArea);
        scrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED);
        scrollPane.setBorder(null);
        
        infoPanel.add(scrollPane, BorderLayout.CENTER);
        
        panel.add(buttonPanel, BorderLayout.NORTH);
        panel.add(infoPanel, BorderLayout.CENTER);
        
        return panel;
    }
    
    // Create nodes and roads panel
    private JPanel createNodesRoadsPanel() {
        JPanel panel = new JPanel(new BorderLayout(15, 15));
        panel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));
        
        // Button Panel with better design
        JPanel buttonPanel = new JPanel();
        buttonPanel.setBackground(new Color(255, 255, 255));
        buttonPanel.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(220, 220, 220), 1),
            BorderFactory.createEmptyBorder(20, 20, 20, 20)
        ));
        buttonPanel.setLayout(new FlowLayout(FlowLayout.CENTER, 30, 20));
        
        JButton getNodesButton = new JButton("Get Nodes");
        getNodesButton.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        getNodesButton.setBackground(new Color(155, 89, 182));
        getNodesButton.setForeground(Color.BLACK);
        getNodesButton.setFocusPainted(false);
        getNodesButton.setPreferredSize(new Dimension(160, 45));
        getNodesButton.setBorder(BorderFactory.createLineBorder(new Color(142, 68, 173), 1));
        getNodesButton.addActionListener(e -> {
            nodesRoadsArea.setText("Getting nodes list...");
            new Thread(() -> {
                try {
                    String nodes = getNodes();
                    SwingUtilities.invokeLater(() -> nodesRoadsArea.setText(nodes));
                } catch (Exception ex) {
                    SwingUtilities.invokeLater(() -> nodesRoadsArea.setText("Error: " + ex.getMessage()));
                }
            }).start();
        });
        
        JButton getRoadsButton = new JButton("Get Roads");
        getRoadsButton.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        getRoadsButton.setBackground(new Color(231, 76, 60));
        getRoadsButton.setForeground(Color.BLACK);
        getRoadsButton.setFocusPainted(false);
        getRoadsButton.setPreferredSize(new Dimension(160, 45));
        getRoadsButton.setBorder(BorderFactory.createLineBorder(new Color(192, 57, 43), 1));
        getRoadsButton.addActionListener(e -> {
            nodesRoadsArea.setText("Getting roads list...");
            new Thread(() -> {
                try {
                    String roads = getRoads();
                    SwingUtilities.invokeLater(() -> nodesRoadsArea.setText(roads));
                } catch (Exception ex) {
                    SwingUtilities.invokeLater(() -> nodesRoadsArea.setText("Error: " + ex.getMessage()));
                }
            }).start();
        });
        
        buttonPanel.add(getNodesButton);
        buttonPanel.add(getRoadsButton);
        
        // Nodes and Roads Area with better design
        JPanel nodesRoadsPanel = new JPanel(new BorderLayout());
        nodesRoadsPanel.setBackground(new Color(255, 255, 255));
        nodesRoadsPanel.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(220, 220, 220), 1),
            BorderFactory.createEmptyBorder(15, 15, 15, 15)
        ));
        
        nodesRoadsArea = new JTextArea();
        nodesRoadsArea.setEditable(false);
        nodesRoadsArea.setFont(new Font("Consolas", Font.PLAIN, 13));
        nodesRoadsArea.setBackground(new Color(248, 249, 250));
        nodesRoadsArea.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(220, 220, 220), 1),
            BorderFactory.createEmptyBorder(10, 12, 10, 12)
        ));
        JScrollPane scrollPane = new JScrollPane(nodesRoadsArea);
        scrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED);
        scrollPane.setBorder(null);
        
        nodesRoadsPanel.add(scrollPane, BorderLayout.CENTER);
        
        panel.add(buttonPanel, BorderLayout.NORTH);
        panel.add(nodesRoadsPanel, BorderLayout.CENTER);
        
        return panel;
    }
    
    // Create system stats panel
    private JPanel createSystemStatsPanel() {
        JPanel panel = new JPanel(new BorderLayout(15, 15));
        panel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));
        
        // Button Panel with better design
        JPanel buttonPanel = new JPanel();
        buttonPanel.setBackground(new Color(255, 255, 255));
        buttonPanel.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(220, 220, 220), 1),
            BorderFactory.createEmptyBorder(20, 20, 20, 20)
        ));
        buttonPanel.setLayout(new FlowLayout(FlowLayout.CENTER, 20, 20));
        
        JButton getStatsButton = new JButton("Get System Stats");
        getStatsButton.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        getStatsButton.setBackground(new Color(142, 68, 173));
        getStatsButton.setForeground(Color.BLACK);
        getStatsButton.setFocusPainted(false);
        getStatsButton.setPreferredSize(new Dimension(200, 45));
        getStatsButton.setBorder(BorderFactory.createLineBorder(new Color(123, 52, 152), 1));
        getStatsButton.addActionListener(e -> {
            statsArea.setText("Getting system stats...");
            new Thread(() -> {
                try {
                    String stats = getSystemStats();
                    SwingUtilities.invokeLater(() -> statsArea.setText(stats));
                } catch (Exception ex) {
                    SwingUtilities.invokeLater(() -> statsArea.setText("Error: " + ex.getMessage()));
                }
            }).start();
        });
        
        buttonPanel.add(getStatsButton);
        
        // Stats Area with better design
        JPanel statsPanel = new JPanel(new BorderLayout());
        statsPanel.setBackground(new Color(255, 255, 255));
        statsPanel.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(220, 220, 220), 1),
            BorderFactory.createEmptyBorder(15, 15, 15, 15)
        ));
        
        statsArea = new JTextArea();
        statsArea.setEditable(false);
        statsArea.setFont(new Font("Consolas", Font.PLAIN, 13));
        statsArea.setBackground(new Color(248, 249, 250));
        statsArea.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(220, 220, 220), 1),
            BorderFactory.createEmptyBorder(10, 12, 10, 12)
        ));
        JScrollPane scrollPane = new JScrollPane(statsArea);
        scrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED);
        scrollPane.setBorder(null);
        
        statsPanel.add(scrollPane, BorderLayout.CENTER);
        
        panel.add(buttonPanel, BorderLayout.NORTH);
        panel.add(statsPanel, BorderLayout.CENTER);
        
        return panel;
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
                    String allPaths = extractAllPaths(responseString);

                    final String resultText = String.format(
                            "Path Planning Success!\n" +
                            "Recommended Path: %s\n" +
                            "Estimated Time: %s seconds\n" +
                            "Route Details: %s\n\n" +
                            "%s",
                            path, duration, message, allPaths
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
            String message = json.substring(messageStart + 10, messageEnd);
            return message.isEmpty() ? "Good traffic" : message;
        }
        return "Good traffic";
    }

    private String extractAllPaths(String json) {
        int allPathsStart = json.indexOf("\"all_paths\":[");
        if (allPathsStart == -1) {
            return "No alternative paths available";
        }
        
        int allPathsEnd = json.lastIndexOf("]");
        if (allPathsEnd == -1) {
            return "No alternative paths available";
        }
        
        String allPathsStr = json.substring(allPathsStart + 12, allPathsEnd);
        if (allPathsStr.isEmpty() || allPathsStr.equals("null")) {
            return "No alternative paths available";
        }
        
        StringBuilder pathsBuilder = new StringBuilder();
        pathsBuilder.append("Route Options:\n");
        pathsBuilder.append("=====================================\n\n");
        
        // Split paths (simple parsing, assuming each path is an object)
        String[] paths = allPathsStr.split("\\}");
        int pathIndex = 1;
        
        // Track best paths for comparison
        double minDistance = Double.MAX_VALUE;
        double minDuration = Double.MAX_VALUE;
        double minCongestion = Double.MAX_VALUE;
        
        // First pass to find best values
        for (String path : paths) {
            if (path.trim().isEmpty()) continue;
            
            String distance = extractDistanceFromPathDetail(path);
            String duration = extractDurationFromPathDetail(path);
            String congestion = extractCongestionFromPathDetail(path);
            
            try {
                double distanceValue = Double.parseDouble(distance);
                double durationValue = Double.parseDouble(duration);
                double congestionValue = Double.parseDouble(congestion);
                
                if (distanceValue < minDistance) minDistance = distanceValue;
                if (durationValue < minDuration) minDuration = durationValue;
                if (congestionValue < minCongestion) minCongestion = congestionValue;
            } catch (NumberFormatException e) {
                // Ignore parsing errors
            }
        }
        
        // Second pass to display paths with comparison
        for (String path : paths) {
            if (path.trim().isEmpty()) continue;
            
            // Extract label
            String label = extractPathLabel(path);
            // Extract path nodes
            String pathNodes = extractPathFromPathDetail(path);
            // Extract distance
            String distance = extractDistanceFromPathDetail(path);
            // Extract duration
            String duration = extractDurationFromPathDetail(path);
            // Extract congestion
            String congestion = extractCongestionFromPathDetail(path);
            
            if (!pathNodes.equals("Unknown")) {
                // Generate friendly label based on path attributes
                String friendlyLabel = getFriendlyLabel(label, distance, duration, congestion);
                
                // Add path header with style
                pathsBuilder.append(String.format("%d. %s\n", pathIndex, friendlyLabel));
                pathsBuilder.append("   --------------------------------\n");
                
                // Format route with arrows
                String formattedRoute = formatRoute(pathNodes);
                pathsBuilder.append(String.format("   Route: %s\n", formattedRoute));
                
                // Add distance with comparison
                try {
                    double distanceValue = Double.parseDouble(distance);
                    String distanceComparison = distanceValue == minDistance ? " (Shortest)" : "";
                    pathsBuilder.append(String.format("   Distance: %s km%s\n", distance, distanceComparison));
                } catch (NumberFormatException e) {
                    pathsBuilder.append(String.format("   Distance: %s km\n", distance));
                }
                
                // Add duration with comparison
                try {
                    double durationValue = Double.parseDouble(duration);
                    String durationComparison = durationValue == minDuration ? " (Fastest)" : "";
                    pathsBuilder.append(String.format("   Time: %s seconds%s\n", duration, durationComparison));
                } catch (NumberFormatException e) {
                    pathsBuilder.append(String.format("   Time: %s seconds\n", duration));
                }
                
                // Add congestion with level
                String congestionLevel = getCongestionLevel(congestion);
                try {
                    double congestionValue = Double.parseDouble(congestion);
                    String congestionComparison = congestionValue == minCongestion ? " (Most Smooth)" : "";
                    pathsBuilder.append(String.format("   Congestion: %s%s\n", congestionLevel, congestionComparison));
                } catch (NumberFormatException e) {
                    pathsBuilder.append(String.format("   Congestion: %s\n", congestionLevel));
                }
                
                // Add road type analysis
                String roadAnalysis = analyzeRoadType(pathNodes);
                if (!roadAnalysis.isEmpty()) {
                    pathsBuilder.append(String.format("   Road Type: %s\n", roadAnalysis));
                }
                
                // Add estimated fuel consumption
                String fuelEstimate = estimateFuelConsumption(distance, congestion);
                pathsBuilder.append(String.format("   Fuel Estimate: %s\n", fuelEstimate));
                
                pathsBuilder.append("\n");
                pathIndex++;
            }
        }
        
        pathsBuilder.append("=====================================\n");
        pathsBuilder.append("Tip: Choose the route that best suits your needs\n");
        
        return pathsBuilder.toString();
    }

    private String extractPathLabel(String pathDetail) {
        int labelStart = pathDetail.indexOf("\"label\":\"");
        if (labelStart != -1) {
            int labelEnd = pathDetail.indexOf("\"", labelStart + 8);
            if (labelEnd != -1) {
                return pathDetail.substring(labelStart + 8, labelEnd);
            }
        }
        return "Unlabeled Path";
    }

    private String extractPathFromPathDetail(String pathDetail) {
        int pathStart = pathDetail.indexOf("\"path\":[");
        int pathEnd = pathDetail.indexOf("]", pathStart);
        if (pathStart != -1 && pathEnd != -1) {
            return pathDetail.substring(pathStart + 8, pathEnd).replace("\"", "").replace(",", " -> ");
        }
        return "Unknown";
    }

    private String extractDistanceFromPathDetail(String pathDetail) {
        int distanceStart = pathDetail.indexOf("\"distance\":");
        if (distanceStart != -1) {
            int commaIndex = pathDetail.indexOf(",", distanceStart);
            if (commaIndex != -1) {
                String distance = pathDetail.substring(distanceStart + 10, commaIndex).trim();
                // Remove extra colons
                return distance.replace(":", "");
            }
        }
        return "0";
    }

    private String extractDurationFromPathDetail(String pathDetail) {
        int durationStart = pathDetail.indexOf("\"duration\":");
        if (durationStart != -1) {
            int commaIndex = pathDetail.indexOf(",", durationStart);
            if (commaIndex != -1) {
                return pathDetail.substring(durationStart + 11, commaIndex).trim();
            }
        }
        return "0";
    }

    private String extractCongestionFromPathDetail(String pathDetail) {
        int congestionStart = pathDetail.indexOf("\"congestion\":");
        if (congestionStart != -1) {
            int commaIndex = pathDetail.indexOf(",", congestionStart);
            if (commaIndex != -1) {
                String congestion = pathDetail.substring(congestionStart + 12, commaIndex).trim();
                // Remove extra colons
                return congestion.replace(":", "");
            }
        }
        return "0";
    }

    // Get friendly path label
    private String getFriendlyLabel(String label, String distance, String duration, String congestion) {
        switch (label) {
            case "shortest_distance":
                return "Shortest Route";
            case "fastest_time":
                return "Fastest Route";
            case "most_smooth":
                return "Most Smooth Route";
            case "recommended":
                return "Recommended Route";
            default:
                // Generate label based on path attributes
                try {
                    double distanceValue = Double.parseDouble(distance);
                    double durationValue = Double.parseDouble(duration);
                    double congestionValue = Double.parseDouble(congestion);
                    
                    if (distanceValue < 3.0) {
                        return "Shorter Distance";
                    } else if (durationValue < 150.0) {
                        return "Shorter Time";
                    } else if (congestionValue < 2.0) {
                        return "Less Congested";
                    } else {
                        return "Alternative Route";
                    }
                } catch (NumberFormatException e) {
                    return "Alternative Route";
                }
        }
    }

    // Get congestion level description
    private String getCongestionLevel(String congestion) {
        try {
            double congestionValue = Double.parseDouble(congestion);
            if (congestionValue < 1.0) {
                return "Smooth";
            } else if (congestionValue < 2.0) {
                return "Light Congestion";
            } else if (congestionValue < 3.0) {
                return "Medium Congestion";
            } else {
                return "Heavy Congestion";
            }
        } catch (NumberFormatException e) {
            return "Unknown";
        }
    }

    // Format route with better styling
    private String formatRoute(String pathNodes) {
        // Replace simple arrows with standard arrows
        return pathNodes.replace(" -> ", " -> ");
    }

    // Analyze road type based on route length and nodes
    private String analyzeRoadType(String pathNodes) {
        String[] nodes = pathNodes.split(" -> ");
        int nodeCount = nodes.length;
        
        if (nodeCount <= 3) {
            return "Local Roads";
        } else if (nodeCount <= 5) {
            return "Urban Roads";
        } else if (nodeCount <= 8) {
            return "Highway";
        } else {
            return "Expressway";
        }
    }

    // Estimate fuel consumption based on distance and congestion
    private String estimateFuelConsumption(String distance, String congestion) {
        try {
            double distanceValue = Double.parseDouble(distance);
            double congestionValue = Double.parseDouble(congestion);
            
            // Simple fuel consumption model: base consumption + congestion factor
            double baseConsumption = distanceValue * 0.1;
            double congestionFactor = 1.0 + (congestionValue * 0.2);
            double totalConsumption = baseConsumption * congestionFactor;
            
            return String.format("%.2f L", totalConsumption);
        } catch (NumberFormatException e) {
            return "Unknown";
        }
    }

    // Get system info
    private String getSystemInfo() throws Exception {
        URL url = new URL("http://localhost:8000/");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        
        int responseCode = conn.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            String inputLine;
            StringBuilder response = new StringBuilder();
            
            while ((inputLine = in.readLine()) != null) {
                response.append(inputLine);
            }
            in.close();
            
            return "System Info:\n" + response.toString();
        } else {
            throw new Exception("HTTP error code: " + responseCode);
        }
    }
    
    // Health check
    private String getHealthCheck() throws Exception {
        URL url = new URL("http://localhost:8000/health");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        
        int responseCode = conn.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            String inputLine;
            StringBuilder response = new StringBuilder();
            
            while ((inputLine = in.readLine()) != null) {
                response.append(inputLine);
            }
            in.close();
            
            return "Health Check:\n" + response.toString();
        } else {
            throw new Exception("HTTP error code: " + responseCode);
        }
    }
    
    // Get nodes list
    private String getNodes() throws Exception {
        URL url = new URL("http://localhost:8000/api/nodes");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        
        int responseCode = conn.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            String inputLine;
            StringBuilder response = new StringBuilder();
            
            while ((inputLine = in.readLine()) != null) {
                response.append(inputLine);
            }
            in.close();
            
            String responseString = response.toString();
            // Parse nodes list
            nodesList.clear();
            int nodesStart = responseString.indexOf("\"nodes\":[");
            int nodesEnd = responseString.indexOf("]", nodesStart);
            if (nodesStart != -1 && nodesEnd != -1) {
                String nodesPart = responseString.substring(nodesStart + 8, nodesEnd);
                String[] nodesArray = nodesPart.split(",");
                for (String node : nodesArray) {
                    String nodeName = node.replace("\"", "").trim();
                    nodesList.add(nodeName);
                }
            }
            
            return "Nodes List:\n" + responseString + "\n\nParsed Nodes: " + nodesList.size() + " nodes";
        } else {
            throw new Exception("HTTP error code: " + responseCode);
        }
    }
    
    // Get roads list
    private String getRoads() throws Exception {
        URL url = new URL("http://localhost:8000/api/roads");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        
        int responseCode = conn.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            String inputLine;
            StringBuilder response = new StringBuilder();
            
            while ((inputLine = in.readLine()) != null) {
                response.append(inputLine);
            }
            in.close();
            
            String responseString = response.toString();
            // Parse roads list
            roadsList.clear();
            int roadsStart = responseString.indexOf("\"roads\":[");
            int roadsEnd = responseString.lastIndexOf("]");
            if (roadsStart != -1 && roadsEnd != -1) {
                String roadsPart = responseString.substring(roadsStart + 8, roadsEnd);
                // Simple count of roads
                int roadCount = roadsPart.split("\\{").length - 1;
                roadsList.add("Total roads: " + roadCount);
            }
            
            return "Roads List:\n" + responseString;
        } else {
            throw new Exception("HTTP error code: " + responseCode);
        }
    }
    
    // Get system stats
    private String getSystemStats() throws Exception {
        URL url = new URL("http://localhost:8000/api/system_stats");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        
        int responseCode = conn.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            String inputLine;
            StringBuilder response = new StringBuilder();
            
            while ((inputLine = in.readLine()) != null) {
                response.append(inputLine);
            }
            in.close();
            
            return "System Statistics:\n" + response.toString();
        } else {
            throw new Exception("HTTP error code: " + responseCode);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            TrafficClient client = new TrafficClient();
            client.setVisible(true);
        });
    }
}
