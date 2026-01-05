import React, { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || ''

function api(path, opts = {}) {
  const url = API_BASE + path
  return axios({ url, ...opts }).then(r => r.data).catch(err => {
    const msg = err?.response?.data?.detail || err.message || 'API error'
    throw new Error(msg)
  })
}

export default function App(){
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [user, setUser] = useState(null)
  const [form, setForm] = useState({username:'', password:''})
  const [msg, setMsg] = useState('')
  const [deposit, setDeposit] = useState(10)
  const [prices, setPrices] = useState({})

  useEffect(()=> {
    if(token){
      localStorage.setItem('token', token)
      loadProfile()
    } else {
      localStorage.removeItem('token')
      setUser(null)
    }
  }, [token])

  async function register(){
    try {
      const r = await api('/register', { method: 'POST', data: form })
      setToken(r.access_token)
      setMsg('Registered & logged in')
    } catch(e){ setMsg('Register: ' + e.message) }
  }

  async function login(){
    try {
      const fd = new URLSearchParams()
      fd.append('username', form.username)
      fd.append('password', form.password)
      const r = await api('/token', { method: 'POST', data: fd })
      setToken(r.access_token)
      setMsg('Logged in')
    } catch(e){ setMsg('Login: ' + e.message) }
  }

  async function loadProfile(){
    try {
      const r = await api('/me', { method: 'GET', headers: { Authorization: 'Bearer ' + token } })
      setUser(r)
    } catch(e){ setMsg('Load: ' + e.message); setToken('') }
  }

  async function depositUsd(){
    try {
      const r = await api('/deposit', { method: 'POST', headers: { Authorization: 'Bearer ' + token }, data: { usd_amount: Number(deposit) } })
      setMsg(`Deposited $${deposit}. Balance: ${r.balance_usd}`)
      loadProfile()
    } catch(e){ setMsg('Deposit: ' + e.message) }
  }

  async function getPrice(t){
    try {
      const r = await api('/price/' + t)
      setPrices(prev => ({...prev, [t]: r.price_usd}))
    } catch(e){ setMsg('Price: ' + e.message) }
  }

  async function spin(){
    try {
      const r = await api('/casino/slots/spin', { method: 'POST', headers: { Authorization: 'Bearer ' + token }, data: { usd_amount: 1 } })
      setMsg(`Spin: ${r.result} payout: ${r.payout}`)
      loadProfile()
    } catch(e){ setMsg('Spin: ' + e.message) }
  }

  async function depositBtc(){
    try {
      const r = await api('/crypto/deposit', { method: 'POST', headers: { Authorization: 'Bearer ' + token }, data: { asset: 'BTC', amount: 0.001 } })
      setMsg(`Crypto deposit credited $${Number(r.usd_credited).toFixed(2)}`)
      loadProfile()
    } catch(e){ setMsg('Crypto deposit: ' + e.message) }
  }

  return (
    <div className="container">
      <div style={{display:'flex',gap:16,alignItems:'center',marginBottom:12}}>
        <h2>IB Crypto Play</h2>
        <div className="small-muted">Demo frontend (Vite)</div>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'320px 1fr',gap:16}}>
        <div className="card">
          <h4>Account</h4>
          {user ? <>
            <div className="small-muted">User</div>
            <div style={{fontWeight:700}}>{user.username}</div>
            <div className="small-muted">Balance</div>
            <div style={{fontSize:18,fontWeight:700}}>USD ${Number(user.balance_usd||0).toFixed(2)}</div>
            <button className="btn btn-primary" style={{marginTop:12}} onClick={()=>{ setToken(''); setMsg('Logged out') }}>Logout</button>
          </> : <>
            <input placeholder="username" value={form.username} onChange={e=>setForm({...form, username:e.target.value})} style={{width:'100%',marginBottom:8}} />
            <input placeholder="password" type="password" value={form.password} onChange={e=>setForm({...form, password:e.target.value})} style={{width:'100%',marginBottom:8}} />
            <div style={{display:'flex',gap:8}}>
              <button className="btn btn-primary" onClick={register}>Register</button>
              <button className="btn" onClick={login}>Login</button>
            </div>
          </>}
        </div>

        <div>
          <div className="card" style={{marginBottom:12}}>
            <h4>Market & Quick Actions</h4>
            <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
              {['BTC','ETH','SOL','BNB'].map(t => <button key={t} className="btn" onClick={()=>getPrice(t)}>{t}</button>)}
              <div style={{marginLeft:'auto',display:'flex',gap:8}}>
                <input type="number" value={deposit} onChange={e=>setDeposit(e.target.value)} style={{width:120}}/>
                <button className="btn btn-primary" onClick={depositUsd} disabled={!token}>Deposit</button>
                <button className="btn" onClick={spin} disabled={!token}>Spin $1</button>
              </div>
            </div>
            <pre>{JSON.stringify(prices)}</pre>
          </div>

          <div className="card">
            <h4>Bet & Crypto Demo</h4>
            <div style={{display:'flex',gap:8}}>
              <button className="btn" onClick={depositBtc} disabled={!token}>Deposit 0.001 BTC</button>
            </div>
            <div style={{marginTop:8}}>
              <div className="small-muted">Messages</div>
              <div>{msg}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
