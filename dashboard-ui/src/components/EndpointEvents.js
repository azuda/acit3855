import React, { useEffect, useState } from 'react';

export default function EndpointEvents() {
    const [counts, setCounts] = useState(null);
    const [error, setError] = useState(null);

    const getEventCounts = () => {
        fetch('http://kafka-acit3855.eastus2.cloudapp.azure.com:8120/event_stats')
            .then(res => res.json())
            .then(
                (result) => {
                    setCounts(result);
                },
                (error) => {
                    setError(error);
                }
            )
    }

    useEffect(() => {
        const interval = setInterval(() => getEventCounts(), 2000); // Update every 2 seconds
        return () => clearInterval(interval);
    }, []);

    if (error) {
        return <div>Error: {error.message}</div>;
    } else if (!counts) {
        return <div>Loading...</div>;
    } else {
        return (
            <div>
                <h2>Logged Event Counts</h2>
                {Object.entries(counts).map(([code, count]) => (
                    <div key={code}>{code}: {count}</div>
                ))}
            </div>
        );
    }
}

