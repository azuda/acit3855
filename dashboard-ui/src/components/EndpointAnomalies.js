import React, { useEffect, useState } from 'react';

function EndpointAnomalies() {
    const [speedId, setSpeedId] = useState(null);
    const [verticalId, setVerticalId] = useState(null);

    useEffect(() => {
        fetch('http://kafka-acit3855.eastus2.cloudapp.azure.com:8130/anomalies?event_type=TooLow')
            .then(response => response.json())
            .then(data => {
                setSpeedId(data.result[0].event_id);
            })
            .catch(error => console.error('Error:', error));

        fetch('http://kafka-acit3855.eastus2.cloudapp.azure.com:8130/anomalies?event_type=TooHigh')
            .then(response => response.json())
            .then(data => {
                setVerticalId(data.result[0].event_id);
            })
            .catch(error => console.error('Error:', error));
    }, []);

    return (
        <div>
            <p>Speed Latest Anomaly UUID: {speedId}</p>
            <p>Vertical Latest Anomaly UUID: {verticalId}</p>
        </div>
    );
}

export default EndpointAnomalies;