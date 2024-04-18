import React, { useEffect, useState } from 'react';

function EndpointAnomalies() {
    const [eventIds, setEventIds] = useState([]);

    useEffect(() => {
        fetch('http://kafka-acit3855.eastus2.cloudapp.azure.com:8130/anomalies')
            .then(response => response.json())
            .then(data => {
                const ids = data.map(event => event.result[0].event_id);
                setEventIds(ids);
            })
            .catch(error => console.error('Error:', error));
    }, []);

    return (
        <div>
            <h2>Latest Event UUIDs</h2>
            {eventIds.map((id, index) => (
                <p key={index}>Event {index + 1}: {id}</p>
            ))}
        </div>
    );
}

export default EndpointAnomalies;