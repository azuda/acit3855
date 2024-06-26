import logo from './logo.png';
import './App.css';

import EndpointAudit from './components/EndpointAudit'
import AppStats from './components/AppStats'
import EndpointEvents from './components/EndpointEvents';
import EndpointAnomalies from './components/EndpointAnomalies';

function App() {

    const endpoints = ["speed", "vertical"]

    const rendered_endpoints = endpoints.map((endpoint) => {
        return <EndpointAudit key={endpoint} endpoint={endpoint}/>
    })

    return (
        <div className="App">
            <img src={logo} className="App-logo" alt="logo" height="200px" width="400px"/>
            <div>
                <AppStats/>
                <h1>Audit Endpoints</h1>
                {rendered_endpoints}
            </div>
            <div>
                <h1>Logged Event Counts</h1>
                <EndpointEvents/>
            </div>
            <div>
                <h1>Anomalies</h1>
                <EndpointAnomalies/>
            </div>
        </div>
    );

}



export default App;
