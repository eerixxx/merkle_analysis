import { Routes, Route } from 'react-router-dom'
import { HomePage } from './pages/Home'
import { LimitlessPage } from './pages/Limitless'
import { BoostyFiPage } from './pages/BoostyFi'
import { LoginPage } from './pages/Login'
import { ProtectedRoute } from './components/ProtectedRoute'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <HomePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/limitless"
        element={
          <ProtectedRoute>
            <LimitlessPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/boostyfi"
        element={
          <ProtectedRoute>
            <BoostyFiPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App
