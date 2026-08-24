import { useEffect, useMemo, useState } from "react";
import { Mail, Phone, RefreshCw, Search, Target, Users, UserRound } from "lucide-react";
import { getOpportunities } from "../api/opportunityApi";
import { getStakeholdersByOpportunity } from "../api/stakeholderApi";
import { ROLES } from "../auth/roles";
import { useAuth } from "../context/AuthContext";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";

export default function Stakeholders(){
 const {activeRole}=useAuth();const[items,setItems]=useState([]);const[search,setSearch]=useState("");const[loading,setLoading]=useState(true);const[error,setError]=useState("");
 const load=async()=>{try{setLoading(true);setError("");const opportunities=await getOpportunities();const groups=await Promise.all(opportunities.map(async opportunity=>({opportunity,stakeholders:await getStakeholdersByOpportunity(opportunity.opportunity_id).catch(()=>[])})));setItems(groups.flatMap(({opportunity,stakeholders})=>stakeholders.map(s=>({...s,opportunity_name:opportunity.opportunity_name}))));}catch(e){setError(e?.response?.data?.message||"Unable to load stakeholders.");}finally{setLoading(false);}};
 useEffect(()=>{if(activeRole===ROLES.SOLUTION_ENGINEER)load();},[activeRole]);
 const q=search.trim().toLowerCase();const visible=useMemo(()=>items.filter(s=>`${s.stakeholder_name||""} ${s.designation||""} ${s.email||""} ${s.opportunity_name||""}`.toLowerCase().includes(q)),[items,q]);
 if(activeRole!==ROLES.SOLUTION_ENGINEER)return <div className="standard-page"><PageHeader title="Stakeholder Mapping" description="This workspace is available to Solution Engineers."/> </div>;
 return <div className="standard-page record-workspace fade-in"><PageHeader title="Stakeholder Mapping" description="Map the people who influence technical decisions across your opportunities." actions={<Button variant="secondary" onClick={load}><RefreshCw size={14}/> Refresh</Button>}/>{error&&<div className="standard-error">{error}</div>}
 <div className="workspace-kpis"><div><Users/><span>Stakeholders</span><strong>{items.length}</strong></div><div><Target/><span>Opportunities</span><strong>{new Set(items.map(x=>x.opportunity_id)).size}</strong></div><div><UserRound/><span>Decision roles</span><strong>{new Set(items.map(x=>x.designation).filter(Boolean)).size}</strong></div><div><Search/><span>Showing</span><strong>{visible.length}</strong></div></div>
 <Card padding={false}><div className="workspace-toolbar"><label className="ui-search"><Search size={14}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search people, roles, email or opportunity…"/></label></div>
 {loading?<div className="table-loading">Loading stakeholders…</div>:!visible.length?<EmptyState message={q?"No stakeholders match your search.":"No authorized stakeholders found."}/>:<div className="stakeholder-grid">{visible.map(s=><article className="stakeholder-card" key={s.stakeholder_id}><div className="stakeholder-avatar">{(s.stakeholder_name||"?").split(/\s+/).map(x=>x[0]).slice(0,2).join("").toUpperCase()}</div><div className="stakeholder-body"><div className="stakeholder-head"><div><strong>{s.stakeholder_name||"Unnamed stakeholder"}</strong><small>{s.designation||"Stakeholder"}</small></div></div><p className="stakeholder-opportunity">{s.opportunity_name}</p><div className="stakeholder-contact">{s.email&&<span><Mail size={13}/>{s.email}</span>}{s.phone&&<span><Phone size={13}/>{s.phone}</span>}</div></div></article>)}</div>}
 </Card></div>;
}