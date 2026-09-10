import { ROLES } from "../auth/roles";
const business=["Dashboard","Opportunities","Accounts","Stakeholders","OEM Registry","POCs"];
const pathMap={"Dashboard":"/dashboard","Opportunities":"/opportunities","Accounts":"/accounts","Stakeholders":"/stakeholders","OEM Registry":"/oem-registry","POCs":"/pocs"};
const navigation={
 [ROLES.LEADERSHIP]:[...business.map(name=>({name,path:pathMap[name]})),{name:"Administration",path:"/admin/users"}],
 [ROLES.ADMIN]:[{name:"Dashboard",path:"/dashboard"},{name:"Administration",path:"/admin/users"}],
 [ROLES.SALES_EXECUTIVE]:business.map(name=>({name,path:pathMap[name]})),
 [ROLES.SALES_MANAGER]:[...business.map(name=>({name,path:pathMap[name]})),{name:"Review Queue",path:"/sales-manager/review"},{name:"Team Performance",path:"/sales-manager/team-performance"}],
 [ROLES.PRE_SALES_MANAGER]:[...business.map(name=>({name,path:pathMap[name]})),{name:"Pending Technical Assignment",path:"/pre-sales/assignments"},{name:"Team Performance",path:"/pre-sales/team-performance"}],
 [ROLES.SOLUTION_ENGINEER]:business.map(name=>({name,path:pathMap[name]})),
 [ROLES.DELIVERY_MANAGER]:business.map(name=>({name,path:pathMap[name]})),
 [ROLES.DEVOPS_ENGINEER]:business.map(name=>({name,path:pathMap[name]})),
 [ROLES.DATA_ANALYST]:business.map(name=>({name,path:pathMap[name]})),
}; export default navigation;
