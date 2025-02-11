import ChatWindow from './components/ChatWindow'
import './index.css'

function App() {
  return (
    <div className="App">
      <header className="header">
        <h1>智能助手</h1>
        <small>Powered by GPT-4</small>
      </header>
      <ChatWindow />
    </div>
  )
}

export default App