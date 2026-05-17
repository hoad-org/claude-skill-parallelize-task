const WS_BASE_URL = process.env.WS_BASE_URL || 'ws://localhost:8000'

export class WebSocketService {
  constructor() {
    this.connections = {}
    this.listeners = {}
  }

  connect(path, onMessage, onError) {
    const url = `${WS_BASE_URL}${path}`

    try {
      const ws = new WebSocket(url)

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (onMessage) {
            onMessage(data)
          }
          // Trigger listeners
          this.notify(path, data)
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      ws.onerror = (error) => {
        console.error(`WebSocket error on ${path}:`, error)
        if (onError) {
          onError(error)
        }
      }

      ws.onclose = () => {
        console.log(`WebSocket closed: ${path}`)
        delete this.connections[path]
      }

      this.connections[path] = ws
      return ws
    } catch (e) {
      console.error(`Failed to connect to ${path}:`, e)
      if (onError) {
        onError(e)
      }
    }
  }

  disconnect(path) {
    if (this.connections[path]) {
      this.connections[path].close()
      delete this.connections[path]
    }
  }

  send(path, data) {
    if (this.connections[path] && this.connections[path].readyState === WebSocket.OPEN) {
      this.connections[path].send(JSON.stringify(data))
    }
  }

  subscribe(path, callback) {
    if (!this.listeners[path]) {
      this.listeners[path] = []
    }
    this.listeners[path].push(callback)

    return () => {
      this.listeners[path] = this.listeners[path].filter(cb => cb !== callback)
    }
  }

  notify(path, data) {
    if (this.listeners[path]) {
      this.listeners[path].forEach(callback => callback(data))
    }
  }

  disconnectAll() {
    Object.keys(this.connections).forEach(path => {
      this.disconnect(path)
    })
  }
}

export const wsService = new WebSocketService()
