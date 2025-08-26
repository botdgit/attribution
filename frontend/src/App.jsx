import React, {useEffect, useState} from 'react'

export default function App(){
  const [status, setStatus] = useState('unknown')

  useEffect(()=>{
    fetch('/health')
      .then(r=>r.json())
      .then(d=>setStatus(d.status))
      .catch(()=>setStatus('unreachable'))
  },[])

  return (
    <div style={{fontFamily:'system-ui, sans-serif', padding:20}}>
      <h1>CFAP Frontend</h1>
      <p>Backend health: <strong>{status}</strong></p>
    </div>
  )
}
