import { useEffect,useMemo,useState } from "react";
import { Building2, RefreshCw, Plus, Archive, Ban, ShieldCheck } from "lucide-react";
import { getAccounts,createAccount,archiveAccount,banAccount,unbanAccount } from "../api/accountApi";
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

 const handleArchive = async (account) => {
   if (!window.confirm(`Archive "${account.account_name}"? This will prevent it from being selected for new opportunities.`)) {
     return;
   }

   try {
     setError("");
     await archiveAccount(account.account_id);
     await load();
   } catch (x) {
     setError(x?.response?.data?.message || "Archive failed");
   }
 };

 const handleBan = async (account) => {
   if (!window.confirm(`Ban "${account.account_name}"? This will prevent it from being selected for new opportunities.`)) {
     return;
   }

   try {
     setError("");
     await banAccount(account.account_id);
     await load();
   } catch (x) {
     setError(x?.response?.data?.message || "Ban failed");
   }
 };

 const handleUnban = async (account) => {
   if (!window.confirm(`Unban "${account.account_name}" and make it Active again?`)) {
     return;
   }

   try {
     setError("");
     await unbanAccount(account.account_id);
     await load();
   } catch (x) {
     setError(x?.response?.data?.message || "Unban failed");
   }
 };

 return <div className="standard-page"><PageHeader title="Accounts" description="Canonical company directory. Accounts are separate from Opportunity pipeline views." actions={<><Button variant="secondary" onClick={load}><RefreshCw size={14}/>Refresh</Button><Button onClick={()=>setShow(!show)}><Plus size={14}/>Create Account</Button></>}/>{error&&<div className="standard-error">{error}</div>}{show&&<Card><form onSubmit={submit} style={{display:"grid",gap:10}}><input required placeholder="Company name" value={form.account_name} onChange={e=>setForm({...form,account_name:e.target.value})}/><input placeholder="Industry" value={form.industry} onChange={e=>setForm({...form,industry:e.target.value})}/><input placeholder="Website" value={form.website} onChange={e=>setForm({...form,website:e.target.value})}/><Button type="submit">Save Account</Button></form></Card>}<Card padding={false}><div className="exec-record-toolbar"><SearchInput value={q} onChange={setQ} placeholder="Search accounts..."/></div>{visible.length?<div className="exec-account-grid">{visible.map(a => {
  const isActive = a.status === "Active";
  const isBanned = a.status === "Banned";
  const isArchived = a.status === "Archived";

  return (
    <div
      key={a.account_id}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: 16,
        borderBottom: "1px solid var(--border)",
        background: isBanned ? "#fff1f2" : "transparent",
        borderLeft: isBanned ? "4px solid #dc2626" : "4px solid transparent",
      }}
    >
      <span className="exec-account-avatar">
        <Building2 size={18}/>
      </span>

      <div style={{flex:1}}>
        <strong>{a.account_name}</strong>
        <span>{a.industry || "Industry not specified"}</span>

        <small
          style={{
            color: isBanned
              ? "#dc2626"
              : isArchived
                ? "#6b7280"
                : "inherit",
            fontWeight: isBanned ? 700 : 500,
          }}
        >
          Status: {a.status}
        </small>
      </div>

      {leadership && isActive && (
        <>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => handleArchive(a)}
          >
            <Archive size={13}/>
            Archive
          </Button>

          <Button
            size="sm"
            variant="secondary"
            onClick={() => handleBan(a)}
          >
            <Ban size={13}/>
            Ban
          </Button>
        </>
      )}

      {leadership && isBanned && (
        <Button
          size="sm"
          variant="secondary"
          onClick={() => handleUnban(a)}
        >
          <ShieldCheck size={13}/>
          Unban
        </Button>
      )}
    </div>
  );
})}</div>:<EmptyState message="No matching accounts."/>}</Card></div>;
}