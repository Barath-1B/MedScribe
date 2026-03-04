import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Overview from './pages/Overview';
import Pipeline from './pages/Pipeline';
import Degradation from './pages/Degradation';
import PerDocument from './pages/PerDocument';
import ErrorBreakdown from './pages/ErrorBreakdown';
import Inspector from './pages/Inspector';
import Upload from './pages/Upload';
import Experiment from './pages/Experiment';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/pipeline" element={<Pipeline />} />
            <Route path="/degradation" element={<Degradation />} />
            <Route path="/documents" element={<PerDocument />} />
            <Route path="/errors" element={<ErrorBreakdown />} />
            <Route path="/inspector" element={<Inspector />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/experiment" element={<Experiment />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
