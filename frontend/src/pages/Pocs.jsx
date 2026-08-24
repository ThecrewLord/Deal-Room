import { useEffect, useMemo, useState } from "react";
import { CalendarDays, CheckCircle2, Clock3, FlaskConical, RefreshCw, Search, Target } from "lucide-react";
import { getOpportunities } from "../api/opportunityApi";
import { getPocsByOpportunity } from "../api/pocApi";
import { ROLES } from "../auth/roles";
import { useAuth } from "../context/AuthContext";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import StatusBadge from "../components/ui/StatusBadge";
import EmptyState from "../components/ui/EmptyState";

export default function Pocs() {
 const {activeRole}=useAuth(); const [items,setItems]=useState([]); const [search,setSearch]=useState(""); const [filter,setFilter]=useState("All"); const [loading,setLoading]=useState(true); const [error,setError]=useState("");
 const load=async()=>{try{setLoading(true);setError("");const opportunities=await getOpportunities();const groups=await Promise.all(opportunities.map(async opportunity=>({opportunity,pocs:await getPocsByOpportunity(opportunity.opportunity_id).catch(()=>[])})));setItems(groups.flatMap(({opportunity,pocs})=>pocs.map(p=>({...p,opportunity_name:opportunity.opportunity_name}))));}catch(e){setError(e?.response?.data?.message||"Unable to load POCs.");}finally{setLoading(false);}};
 useEffect(()=>{if(activeRole===ROLES.SOLUTION_ENGINEER)load();},[activeRole]);
 const q=search.trim().toLowerCase(); const visible=useMemo(()=>items.filter(p=>{const text=`${p.poc_name||""} ${p.opportunity_name||""} ${p.status||""}`.toLowerCase();return(!q||text.includes(q))&&(filter==="All"||p.status===filter)}),[items,q,filter]);
 const active=items.filter(p=>["Approved","In Progress","Submitted"].includes(p.status)).length;
 if(activeRole!==ROLES.SOLUTION_ENGINEER)return <div className="standard-page"><PageHeader title="POC Tracker" description="This workspace is available to Solution Engineers." /></div>;
 return <div className="standard-page record-workspace fade-in"><PageHeader title="POC Tracker" description="Plan, execute and close technical proofs of concept." actions={<Button variant="secondary" onClick={load}><RefreshCw size={14}/> Refresh</Button>}/>
 {error&&<div className="standard-error">{error}</div>}
 <div className="workspace-kpis"><div><FlaskConical/><span>Total POCs</span><strong>{items.length}</strong></div><div><Clock3/><span>Active</span><strong>{active}</strong></div><div><CheckCircle2/><span>Completed</span><strong>{items.filter(p=>p.status==="Completed").length}</strong></div><div><Target/><span>Showing</span><strong>{visible.length}</strong></div></div>
 <Card padding={false}><div className="workspace-toolbar"><label className="ui-search"><Search size={14}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search POCs, opportunities or status…"/></label><div className="workspace-filters">{["All","Approved","In Progress","Submitted","Completed","Rejected"].map(s=><button key={s} className={filter===s?"active":""} onClick={()=>setFilter(s)}>{s}</button>)}</div></div>
 {loading?<div className="table-loading">Loading POCs…</div>:!visible.length?<EmptyState message={q||filter!=="All"?"No POCs match your filters.":"No POCs found for your authorized opportunities."}/>:<div className="workspace-table"><div className="workspace-table-head"><span>POC</span><span>Opportunity</span><span>Status</span><span>Target date</span><span>Outcome</span></div>{visible.map(p=><div className="workspace-table-row" key={p.poc_id}><div><strong>{p.poc_name||"Untitled POC"}</strong><small>{p.objective||"Technical validation"}</small></div><div className="wrap-cell">{p.opportunity_name}</div><StatusBadge status={p.status}/><div><CalendarDays size={13}/> {p.target_date||"—"}</div><div className="wrap-cell">{p.outcome||"—"}</div></div>)}</div>}
 </Card></div>;
}