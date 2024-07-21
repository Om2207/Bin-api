<?php
// Path to your CSV file
$csvFile = 'bins.csv';

// Function to read the CSV file and return the BIN data as an associative array
function getBinData($bin, $csvFile) {
    if (!file_exists($csvFile) || !is_readable($csvFile)) {
        error_log("CSV file is missing or not readable");
        return ['error' => 'CSV file is missing or not readable'];
    }

    $data = [];
    $columns = ['BIN', 'Country Code', 'Country Emoji', 'Card Type', 'Credit/Debit', 'Brand', 'Issuer'];

    if (($handle = fopen($csvFile, 'r')) !== false) {
        while (($row = fgetcsv($handle, 1000, ',')) !== false) {
            $rowData = array_combine($columns, $row);
            if ($rowData['BIN'] === $bin) {
                $data = $rowData;
                break;
            }
        }
        fclose($handle);
    } else {
        error_log("Failed to open the CSV file");
        return ['error' => 'Failed to open the CSV file'];
    }
    return $data ?: ['error' => 'BIN not found'];
}

// Get the BIN from the query parameter
$bin = isset($_GET['Bin']) ? $_GET['Bin'] : '';
error_log("BIN parameter: $bin");

header('Content-Type: application/json');
if ($bin) {
    $binData = getBinData($bin, $csvFile);

    if (isset($binData['error'])) {
        error_log("Error response: " . json_encode($binData, JSON_PRETTY_PRINT));
        echo json_encode($binData, JSON_PRETTY_PRINT);
    } else {
        $response = [
            'BIN' => $binData['BIN'],
            'Country Code' => $binData['Country Code'],
            'Country Emoji' => $binData['Country Emoji'],
            'Card Type' => $binData['Card Type'],
            'Credit/Debit' => $binData['Credit/Debit'],
            'Brand' => $binData['Brand'],
            'Issuer' => $binData['Issuer']
        ];
        error_log("BIN data for JSON response: " . json_encode($response, JSON_PRETTY_PRINT));
        echo json_encode($response, JSON_PRETTY_PRINT);
    }
} else {
    $error_response = ['error' => 'No BIN provided'];
    error_log("No BIN provided response: " . json_encode($error_response, JSON_PRETTY_PRINT));
    echo json_encode($error_response, JSON_PRETTY_PRINT);
}
?>
