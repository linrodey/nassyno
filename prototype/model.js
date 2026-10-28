(function(root){
const devices=[{id:'site',name:'NAS-SITE-DEMO',site:'Công trình',model:'RS2423RP+II',online:true,cpu:18,ram:42,total:32,used:23},{id:'office',name:'NAS-OFFICE-DEMO',site:'Văn phòng',model:'DS1821+',online:true,cpu:35,ram:61,total:24,used:21.6},{id:'backup',name:'NAS-BACKUP-DEMO',site:'Trung tâm',model:'RS1221+',online:false,total:null,used:null}];
const users=[{name:'nguyen.an',source:'Thủ công',group:'IT'},{name:'tran.binh',source:'LDAP',group:'Kỹ thuật'},{name:'le.chi',source:'Portal Office',group:'Công trình'}];
function totals(ds){const valid=ds.filter(d=>d.online&&Number.isFinite(d.total)&&Number.isFinite(d.used));return {total:valid.reduce((n,d)=>n+d.total,0),used:valid.reduce((n,d)=>n+d.used,0),missing:ds.length-valid.length};}
function filterUsers(q,s){return users.filter(u=>(!s||u.source===s)&&u.name.toLowerCase().includes(q.toLowerCase()));}
function preview(kind,value){if(kind==='acl'){if(!['Đọc','Đọc / Ghi'].includes(value))throw Error('Quyền không hợp lệ');return 'Nhóm KYTHUAT: Đọc → '+value+'. Chỉ thư mục này; không áp đệ quy. Chưa tính quyền hiệu lực; không gửi lệnh.';}if(kind==='ip'){const p=value.trim().split('.');if(p.length!==4||p.some(x=>!/^\d{1,3}$/.test(x)||Number(x)>255))throw Error('Nhập IPv4 hợp lệ');return 'Đề xuất chặn '+value.trim()+'. Chưa xác minh thứ tự luật và đường khôi phục; thực thi bị khóa.';}throw Error('Loại thay đổi không hợp lệ');}
const api={devices,users,totals,filterUsers,preview};if(typeof module!=='undefined')module.exports=api;root.NasDemo=api;
})(globalThis);
