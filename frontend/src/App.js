import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainView from './pages/MainView';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainView />} />
      </Routes>
    </Router>
  );
}

export default App;