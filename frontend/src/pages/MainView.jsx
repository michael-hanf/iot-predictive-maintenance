import Dashboard from './Dashboard';
import ControlPanel from './ControlPanel';

function MainView() {
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Dashboard - 70% */}
      <div className="flex-1 overflow-y-auto">
        <Dashboard />
      </div>

      {/* Control Panel - 30% Sidebar */}
      <div className="w-96 overflow-y-auto border-l border-gray-200">
        <ControlPanel />
      </div>
    </div>
  );
}

export default MainView;