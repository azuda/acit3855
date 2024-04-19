import React, { useEffect, useState } from 'react';

function EndpointAnomalies() {
    const [speedId, setSpeedId] = useState(null);
    const [verticalId, setVerticalId] = useState(null);

    const getEventCounts = () => {
        fetch('http://kafka-acit3855.eastus2.cloudapp.azure.com:8130/anomalies?anomaly_type=TooLow')
            .then(response => response.json())
            .then(data => {
                setSpeedId(data.result[0].event_id);
            })
            .catch(error => console.error('Error:', error));

        fetch('http://kafka-acit3855.eastus2.cloudapp.azure.com:8130/anomalies?anomaly_type=TooHigh')
            .then(response => response.json())
            .then(data => {
                setVerticalId(data.result[0].event_id);
            })
            .catch(error => console.error('Error:', error));
    };

    useEffect(() => {
        getEventCounts(); // Fetch immediately on component mount
        const interval = setInterval(getEventCounts, 2000); // Update every 2 seconds
        return () => clearInterval(interval);
    }, []);

    return (
        <div>
            <p>Speed Latest Anomaly UUID: {speedId}</p>
            <p>Vertical Latest Anomaly UUID: {verticalId}</p>
        </div>
    );
}

export default EndpointAnomalies;