import java.io.BufferedReader;
import java.io.StringReader;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.Stream;

class DataProcessor {
    private List<Map<String, String>> data = new ArrayList<>();
    private Map<String, Integer> wordFrequency = new HashMap<>();
    private static final String CSV_DATA = """
            Order ID,Order Date,Ship Date,Product Name,Sales,Profit,Discount
            CA-2017-152156,08-11-2017,11-11-2017,Staples,261.96,41.91,0.0
            CA-2017-152157,08-11-2017,11-11-2017,Paper,731.94,219.582,0.0
            CA-2017-138688,12-06-2017,16-06-2017,Binders,14.62,6.8714,0.0
            CA-2016-115812,11-10-2016,18-10-2016,Art,22.368,2.5168,0.2
            CA-2015-115812,11-10-2015,18-10-2015,Staples,20.0,3.0,0.1
            CA-2017-152157,08-11-2017,11-11-2017,,731.94,219.582,0.0
            """;

    private static final Map<String, String> PRODUCT_SYNONYMS = Map.of(
        "staples", "stationery",
        "binders", "binder",
        "papers", "paper"
    );

    public void loadData(int limit) {
        Set<String> processedKeys = new HashSet<>();
        try (BufferedReader reader = new BufferedReader(new StringReader(CSV_DATA))) {
            String headerLine = reader.readLine();
            if (headerLine == null) {
                throw new IllegalArgumentException("CSV data is empty or invalid.");
            }

            SimpleDateFormat[] dateFormats = {
                new SimpleDateFormat("dd-MM-yyyy"),
                new SimpleDateFormat("MM-dd-yyyy"),
                new SimpleDateFormat("yyyy-MM-dd")
            };

            String line;
            while ((line = reader.readLine()) != null && data.size() < limit) {
                try {
                    String[] values = line.split(",", -1);
                    if (values.length < 7) {
                        System.err.println("Skipping invalid row: insufficient columns");
                        continue;
                    }

                    Map<String, String> row = new HashMap<>();
                    String orderId = values[0].trim();
                    String productName = values[3].trim().isEmpty() ? "Unknown" : values[3].trim();
                    String compositeKey = orderId + "|" + productName;

                    if (!processedKeys.add(compositeKey)) {
                        System.err.println("Skipping duplicate record: " + compositeKey);
                        continue;
                    }

                    row.put("Order ID", orderId);
                    row.put("Order Date", parseDate(values[1], dateFormats));
                    row.put("Ship Date", parseDate(values[2], dateFormats));
                    row.put("Product Name", productName);
                    row.put("Sales", validateNumeric(values[4], "0.0"));
                    row.put("Profit", validateNumeric(values[5], "0.0"));
                    row.put("Discount", validateNumeric(values[6], "0.0"));

                    if (isValidRow(row)) {
                        data.add(row);
                    }
                } catch (Exception e) {
                    System.err.println("Error processing row: " + e.getMessage());
                }
            }
        } catch (Exception e) {
            System.err.println("Error loading data: " + e.getMessage());
        }
    }

    private String validateNumeric(String value, String defaultValue) {
        if (value == null || value.trim().isEmpty()) {
            return defaultValue;
        }
        try {
            Double.parseDouble(value.trim());
            return value.trim();
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }

    private boolean isValidRow(Map<String, String> row) {
        return isValid(row.get("Sales")) && 
               isValid(row.get("Profit")) && 
               isValid(row.get("Order ID"));
    }

    private String parseDate(String date, SimpleDateFormat[] formats) {
        if (date == null || date.trim().isEmpty()) {
            return "Invalid Date";
        }
        
        for (SimpleDateFormat format : formats) {
            try {
                format.setLenient(false);
                return format.parse(date.trim()).toString();
            } catch (ParseException ignored) {
            }
        }
        return "Invalid Date";
    }

    private boolean isValid(String value) {
        return value != null && !value.trim().isEmpty();
    }

    public void calculateWordFrequencies() {
        Pattern pattern = Pattern.compile("[^a-zA-Z0-9\\s]");
        wordFrequency.clear();

        data.stream()
            .map(row -> row.get("Product Name"))
            .filter(Objects::nonNull)
            .map(name -> pattern.matcher(name.toLowerCase()).replaceAll(""))
            .flatMap(name -> Stream.of(name.split("\\s+")))
            .filter(word -> word.length() > 1 && !isStopWord(word))
            .map(this::normalizeTerm)
            .forEach(word -> wordFrequency.merge(word, 1, Integer::sum));
    }

    private String normalizeTerm(String word) {
        String normalized = word.toLowerCase();
        return PRODUCT_SYNONYMS.getOrDefault(normalized, normalized);
    }

    private boolean isStopWord(String word) {
        Set<String> stopWords = Set.of("the", "and", "of", "in", "on", "to", "for", "with", "by");
        return stopWords.contains(word.toLowerCase());
    }

    public List<Map<String, String>> getData() {
        return data.stream()
            .map(row -> {
                Map<String, String> enrichedRow = new HashMap<>(row);
                if (!row.get("Order Date").equals("Invalid Date") && 
                    !row.get("Ship Date").equals("Invalid Date")) {
                    enrichedRow.put("Shipping Delay", 
                        calculateShippingDelay(row.get("Order Date"), row.get("Ship Date")));
                }
                return enrichedRow;
            })
            .collect(Collectors.toList());
    }

    private String calculateShippingDelay(String orderDate, String shipDate) {
        try {
            long diffInDays = 3; // Placeholder for actual calculation
            return String.valueOf(diffInDays) + " days";
        } catch (Exception e) {
            return "Unknown";
        }
    }

    public Map<String, Integer> getWordFrequencies() {
        return wordFrequency.entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .collect(Collectors.toMap(
                Map.Entry::getKey,
                Map.Entry::getValue,
                (e1, e2) -> e1,
                LinkedHashMap::new
            ));
    }
}