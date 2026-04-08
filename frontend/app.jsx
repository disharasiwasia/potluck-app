const { useState, useEffect } = React;

const API_BASE = "http://127.0.0.1:8000/api";

function App() {
    const [view, setView] = useState("landing");
    const [groupNo, setGroupNo] = useState("");
    const [participantId, setParticipantId] = useState(null);
    const [dashboardData, setDashboardData] = useState(null);
    
    const [name, setName] = useState("");
    const [phone, setPhone] = useState("");
    const [inputGroupNo, setInputGroupNo] = useState("");

    const [showParticipants, setShowParticipants] = useState(false);
    const [itemCategory, setItemCategory] = useState("Main Course");
    const [itemName, setItemName] = useState("");
    
    // Group name edit state
    const [isEditingGroupName, setIsEditingGroupName] = useState(false);
    const [editGroupNameVal, setEditGroupNameVal] = useState("");

    // Item edit state
    const [editingItemId, setEditingItemId] = useState(null);
    const [editItemNameVal, setEditItemNameVal] = useState("");

    const fetchDashboard = async (gNo) => {
        try {
            const res = await fetch(`${API_BASE}/potlucks/${gNo}`);
            if (res.ok) {
                const data = await res.json();
                setDashboardData(data);
            } else {
                alert("Potluck not found!");
                setView("landing");
            }
        } catch (e) {
            console.error(e);
            alert("Error fetching dashboard.");
        }
    };

    const handleCreate = async () => {
        if (!name || !phone) return alert("Please enter name and phone number");
        try {
            const res = await fetch(`${API_BASE}/potlucks`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, phone })
            });
            const data = await res.json();
            setGroupNo(data.group_no);
            setParticipantId(data.participant_id);
            await fetchDashboard(data.group_no);
            setView("dashboard");
        } catch (e) { console.error(e); }
    };

    const handleJoin = async () => {
        if (!name || !phone || !inputGroupNo) return alert("Fill all fields");
        try {
            const res = await fetch(`${API_BASE}/potlucks/${inputGroupNo}/join`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, phone })
            });
            if (!res.ok) return alert("Group not found");
            const data = await res.json();
            setGroupNo(inputGroupNo);
            setParticipantId(data.participant_id);
            await fetchDashboard(inputGroupNo);
            setView("dashboard");
        } catch (e) { console.error(e); }
    };

    const toggleStatus = async (pid, currentStatus) => {
        const newStatus = currentStatus === "coming" ? "not_coming" : "coming";
        try {
            await fetch(`${API_BASE}/participants/${pid}/status`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: newStatus })
            });
            await fetchDashboard(groupNo);
        } catch (e) { console.error(e); }
    };

    const handleAddItem = async () => {
        if (!itemName) return alert("Enter a food name");
        try {
            await fetch(`${API_BASE}/potlucks/${groupNo}/items`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    participant_id: participantId,
                    category: itemCategory,
                    name: itemName
                })
            });
            setItemName("");
            await fetchDashboard(groupNo);
        } catch (e) { console.error(e); }
    };

    const handleUpdateGroupName = async () => {
        if (!editGroupNameVal.trim()) return setIsEditingGroupName(false);
        try {
            await fetch(`${API_BASE}/potlucks/${groupNo}/name`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ group_name: editGroupNameVal })
            });
            setIsEditingGroupName(false);
            await fetchDashboard(groupNo);
        } catch (e) { console.error(e); }
    };

    const handleUpdateItem = async (itemId) => {
        if (!editItemNameVal.trim()) {
             setEditingItemId(null);
             return;
        }
        try {
            await fetch(`${API_BASE}/items/${itemId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: editItemNameVal })
            });
            setEditingItemId(null);
            await fetchDashboard(groupNo);
        } catch (e) { console.error(e); }
    }

    if (view === "landing") {
        return (
            <div className="app-container fade-in">
                <h1 className="text-center">Potluck Party! 🥘</h1>
                <p className="text-center mb-4">The easiest way to organize what everyone brings.</p>
                
                <div className="landing-grid">
                    <div className="card flex-col shadow-sm">
                        <h2>Create New</h2>
                        <input placeholder="Your Name" value={name} onChange={e => setName(e.target.value)} />
                        <input placeholder="Phone Number" type="tel" value={phone} onChange={e => setPhone(e.target.value)} />
                        <button onClick={handleCreate}>Create Potluck</button>
                    </div>
                    
                    <div className="card flex-col shadow-sm">
                        <h2>Join Existing</h2>
                        <input placeholder="Group Number" value={inputGroupNo} onChange={e => setInputGroupNo(e.target.value)} maxLength={6} />
                        <input placeholder="Your Name" value={name} onChange={e => setName(e.target.value)} />
                        <input placeholder="Phone Number" type="tel" value={phone} onChange={e => setPhone(e.target.value)} />
                        <button className="outline" onClick={handleJoin}>Join Potluck</button>
                    </div>
                </div>
            </div>
        );
    }

    if (view === "dashboard" && dashboardData) {
        const comingCount = dashboardData.participants.filter(p => p.status === "coming").length;
        const categories = ["Drinks", "Snacks", "Main Course", "Dessert"];
        
        return (
            <div className="app-container fade-in" style={{ maxWidth: '1000px', width: '100vw' }}>
                <div className="dashboard-header" style={{flexDirection: 'column', alignItems: 'flex-start', cursor: 'default'}}>
                    <div className="flex-row justify-between" style={{width: '100%', alignItems: 'flex-start'}}>
                        <div style={{flex: 1}}>
                            {isEditingGroupName ? (
                                <div className="flex-row items-center">
                                    <input autoFocus value={editGroupNameVal} onChange={e => setEditGroupNameVal(e.target.value)} style={{marginBottom: 0, fontSize: '1.5rem', fontWeight: 'bold'}} />
                                    <button onClick={handleUpdateGroupName}>Save</button>
                                </div>
                            ) : (
                                <h1 style={{display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0'}}>
                                    {dashboardData.group_name} 
                                    <span style={{fontSize: '1rem', cursor: 'pointer', opacity: 0.7}} onClick={() => { setEditGroupNameVal(dashboardData.group_name || ""); setIsEditingGroupName(true); }}>
                                        ✏️
                                    </span>
                                </h1>
                            )}
                            <p className="text-secondary" style={{fontSize: '1rem', marginTop: '0.5rem', marginBottom: 0}}>Group Code: <strong style={{color: 'var(--text-primary)'}}>{groupNo}</strong></p>
                        </div>
                        
                        <div className="coming-count" style={{cursor: 'pointer', textAlign: 'right'}} onClick={() => setShowParticipants(true)}>
                            {comingCount} Coming {comingCount > 0 ? "🔥" : "😢"}
                            <div className="text-secondary" style={{fontSize: '0.8rem', fontWeight: 'normal', marginTop: '4px'}}>Click to view participants</div>
                        </div>
                    </div>
                </div>

                <div className="card mb-4 mt-4" style={{border: '2px solid rgba(245, 158, 11, 0.3)'}}>
                    <h3>Volunteer to bring something!</h3>
                    <div className="flex-row items-center mt-4">
                        <select value={itemCategory} onChange={e => setItemCategory(e.target.value)} style={{marginBottom: 0, flex: 1}}>
                            {categories.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                        <input placeholder="What are you bringing?" value={itemName} onChange={e => setItemName(e.target.value)} style={{marginBottom: 0, flex: 2}} />
                        <button onClick={handleAddItem} style={{flex: 1}}>Add to Menu</button>
                    </div>
                </div>

                <h2 className="mt-4">The Menu</h2>
                <div className="menu-grid mb-4">
                    {categories.map(cat => {
                        const items = dashboardData.items.filter(i => {
                            if (i.category !== cat) return false;
                            const participant = dashboardData.participants.find(p => p.id === i.participant_id);
                            return participant && participant.status === "coming";
                        });
                        return (
                            <div key={cat} className="category-card">
                                <h3 className="category-title">{cat}</h3>
                                {items.length === 0 ? <p className="text-secondary" style={{fontSize: '0.9rem'}}>Nothing yet...</p> : null}
                                {items.map(item => (
                                    <div key={item.id} className="food-item">
                                        {editingItemId === item.id ? (
                                            <div className="flex-row items-center" style={{gap: '0.5rem'}}>
                                                <input autoFocus value={editItemNameVal} onChange={e => setEditItemNameVal(e.target.value)} style={{marginBottom: 0, padding:'0.5rem', width: '100%'}}/>
                                                <button onClick={() => handleUpdateItem(item.id)} style={{padding:'0.5rem 1rem'}}>Save</button>
                                            </div>
                                        ) : (
                                            <div className="flex-row justify-between items-center">
                                                <div>
                                                    <strong>{item.item_name}</strong>
                                                    <div className="food-provider">Brought by {item.participant_name}</div>
                                                </div>
                                                {item.participant_id === participantId && (
                                                    <button className="outline" style={{padding: '0.25rem 0.5rem', fontSize: '0.8rem', border: 'none'}} onClick={() => { setEditItemNameVal(item.item_name); setEditingItemId(item.id); }}>✏️ Edit</button>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        );
                    })}
                </div>

                {showParticipants && (
                    <div className="modal-overlay" onClick={() => setShowParticipants(false)}>
                        <div className="modal-content fade-in" onClick={e => e.stopPropagation()}>
                            <div className="flex-row justify-between mb-4 items-center">
                                <h2 style={{marginBottom: 0}}>Participants ({dashboardData.participants.length})</h2>
                                <button className="outline" onClick={() => setShowParticipants(false)} style={{padding: '0.4rem 0.8rem'}}>X</button>
                            </div>
                            
                            {dashboardData.participants.map(p => (
                                <div key={p.id} className="participant-item">
                                    <div className="flex-col" style={{gap: '0.2rem'}}>
                                        <div className="participant-name">
                                            {p.name}
                                            {p.status === "not_coming" && <span className="sad-emoji">😢</span>}
                                        </div>
                                        <div style={{fontSize: '0.8rem', color: 'var(--text-secondary)'}}>{p.phone}</div>
                                    </div>
                                    <div className="flex-row items-center">
                                        <span className={`badge ${p.status === "coming" ? "coming" : "not-coming"}`}>
                                            {p.status === "coming" ? "Coming" : "Not Coming"}
                                        </span>
                                        {p.id === participantId && (
                                            <button 
                                                className={`outline ${p.status === "coming" ? "danger" : ""}`}
                                                onClick={() => toggleStatus(p.id, p.status)}
                                                style={{padding: '4px 8px', fontSize: '0.8rem', marginLeft: '10px'}}
                                            >
                                                {p.status === "coming" ? "Mark Not Coming" : "Mark Coming"}
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        );
    }

    return <div className="app-container" style={{display: 'flex', justifyContent: 'center', alignItems: 'center'}}><h2>Loading...</h2></div>;
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
