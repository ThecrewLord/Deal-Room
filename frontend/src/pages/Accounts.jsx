import { useEffect,useMemo,useState } from "react";
import { Building2, RefreshCw, Plus, Archive, Ban } from "lucide-react";
import { getAccounts,createAccount,archiveAccount,banAccount } from "../api/accountApi";
import { useAuth } from "../context/AuthContext";
import { ROLES } from "../auth/roles";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import SearchInput from "../components/ui/SearchInput";
import EmptyState from "../components/ui/EmptyState";

export default function Accounts(){
 const {activeRole}=useAuth(); const [rows,setRows]=useState([]); const [q,setQ]=useState(""); const [form,setForm]=useState({account_name:"",industry:"",website:""}); const [show,setShow]=useState(false); const [error,setError]=useState("");
 const load=async()=>{try{setError("");setRows(await getAccounts())}catch(e){setError(e?.response?.data?.message||"Unable to load accounts.")}}; useEffect(()=>{load()},[activeRole]);
 const visible=useMemo(()=>rows.filter(a=>[a.account_name,a.industry,a.city,a.state,a.country].some(v=>String(v||"").toLowerCase().includes(q.toLowerCase()))),[rows,q]);
 const leadership=activeRole===ROLES.LEADERSHIP;
 const submit=async e=>{e.preventDefault();try{await createAccount(form);setForm({account_name:"",industry:"",website:""});setShow(false);load()}catch(x){setError(x?.response?.data?.message||"Unable to create account.")}};
 return <div className="standard-page"><PageHeader title="Accounts" description="Canonical company directory. Accounts are separate from Opportunity pipeline views." actions={<><Button variant="secondary" onClick={load}><RefreshCw size={14}/>Refresh</Button><Button onClick={()=>setShow(!show)}><Plus size={14}/>Create Account</Button></>}/>{error&&<div className="standard-error">{error}</div>}{show&&<Card><form onSubmit={submit} style={{display:"grid",gap:10}}><input required placeholder="Company name" value={form.account_name} onChange={e=>setForm({...form,account_name:e.target.value})}/><input placeholder="Industry" value={form.industry} onChange={e=>setForm({...form,industry:e.target.value})}/><input placeholder="Website" value={form.website} onChange={e=>setForm({...form,website:e.target.value})}/><Button type="submit">Save Account</Button></form></Card>}<Card padding={false}><div className="exec-record-toolbar"><SearchInput value={q} onChange={setQ} placeholder="Search accounts..."/></div>{visible.length?<div className="exec-account-grid">{visible.map(a=><div key={a.account_id} style={{display:"flex",alignItems:"center",gap:12,padding:16,borderBottom:"1px solid var(--border)"}}><span className="exec-account-avatar"><Building2 size={18}/></span><div style={{flex:1}}><strong>{a.account_name}</strong><span>{a.industry||"Industry not specified"}</span><small>Status: {a.status}</small></div>{leadership&&a.status==="Active"&&<><Button size="sm" variant="secondary" onClick={()=>archiveAccount(a.account_id).then(load).catch(x=>setError(x?.response?.data?.message||"Archive failed"))}><Archive size={13}/>Archive</Button><Button size="sm" variant="secondary" onClick={()=>banAccount(a.account_id).then(load).catch(x=>setError(x?.response?.data?.message||"Ban failed"))}><Ban size={13}/>Ban</Button></>}</div>)}</div>:<EmptyState message="No matching accounts."/>}</Card></div>;
}