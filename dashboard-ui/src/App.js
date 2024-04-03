import logo from './logo.png';
import './App.css';

import EndpointAudit from './components/EndpointAudit'
import AppStats from './components/AppStats'
import EndpointEvents from './components/EndpointEvents';

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
                <h1>Event Counts</h1>
                <EndpointEvents/>
            </div>
        </div>
    );

}



export default App;
