import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getCurrentUser,
  getZakatEntries,
  getZakatStatistics,
  createZakat,
  deleteZakat,
} from '../services/api';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import './Dashboard.css';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

function Dashboard() {
  const [user, setUser] = useState(null);
  const [entries, setEntries] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    amount: '',
    category: 'Cash',
    description: '',
  });
  const navigate = useNavigate();

  const categories = ['Cash', 'Gold', 'Silver', 'Business', 'Agriculture', 'Other'];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [userData, entriesData, statsData] = await Promise.all([
        getCurrentUser(),
        getZakatEntries(),
        getZakatStatistics(),
      ]);
      setUser(userData);
      setEntries(entriesData);
      setStatistics(statsData);
    } catch (error) {
      console.error('Error fetching data:', error);
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        navigate('/');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await createZakat({
        amount: parseFloat(formData.amount),
        category: formData.category,
        description: formData.description,
      });
      setFormData({
        amount: '',
        category: 'Cash',
        description: '',
      });
      setShowAddForm(false);
      fetchData();
      alert('Zakat entry added successfully!');
    } catch (error) {
      console.error('Error creating zakat:', error);
      alert('Failed to add zakat entry');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this entry?')) {
      try {
        await deleteZakat(id);
        fetchData();
        alert('Entry deleted successfully!');
      } catch (error) {
        console.error('Error deleting zakat:', error);
        alert('Failed to delete entry');
      }
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  // Prepare chart data
  const categoryData = statistics?.category_breakdown || {};
  const pieData = {
    labels: Object.keys(categoryData),
    datasets: [
      {
        data: Object.values(categoryData).map((cat) => cat.total_amount),
        backgroundColor: [
          '#667eea',
          '#764ba2',
          '#f093fb',
          '#4facfe',
          '#43e97b',
          '#fa709a',
        ],
      },
    ],
  };

  const barData = {
    labels: Object.keys(categoryData),
    datasets: [
      {
        label: 'Zakat Amount',
        data: Object.values(categoryData).map((cat) => cat.total_zakat),
        backgroundColor: '#667eea',
      },
    ],
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Zakat Management System</h1>
        <div className="user-info">
          <span>Welcome, {user?.full_name}!</span>
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
        </div>
      </header>

      <div className="dashboard-content">
        {/* Statistics Cards */}
        <div className="stats-cards">
          <div className="stat-card">
            <h3>Total Amount</h3>
            <p className="stat-value">
              ${statistics?.total_amount?.toFixed(2) || '0.00'}
            </p>
          </div>
          <div className="stat-card">
            <h3>Total Zakat Due</h3>
            <p className="stat-value">
              ${statistics?.total_zakat?.toFixed(2) || '0.00'}
            </p>
          </div>
          <div className="stat-card">
            <h3>Total Entries</h3>
            <p className="stat-value">{statistics?.total_entries || 0}</p>
          </div>
        </div>

        {/* Charts */}
        {statistics && statistics.total_entries > 0 && (
          <div className="charts-container">
            <div className="chart-box">
              <h3>Amount by Category</h3>
              <Pie data={pieData} />
            </div>
            <div className="chart-box">
              <h3>Zakat by Category</h3>
              <Bar data={barData} />
            </div>
          </div>
        )}

        {/* Add Entry Button */}
        <div className="action-buttons">
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="btn-primary"
          >
            {showAddForm ? 'Cancel' : 'Add New Entry'}
          </button>
        </div>

        {/* Add Entry Form */}
        {showAddForm && (
          <div className="add-form">
            <h3>Add Zakat Entry</h3>
            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label>Amount *</label>
                  <input
                    type="number"
                    name="amount"
                    value={formData.amount}
                    onChange={handleChange}
                    required
                    step="0.01"
                    min="0"
                    placeholder="Enter amount"
                  />
                </div>
                <div className="form-group">
                  <label>Category *</label>
                  <select
                    name="category"
                    value={formData.category}
                    onChange={handleChange}
                    required
                  >
                    {categories.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="Enter description (optional)"
                  rows="3"
                />
              </div>
              <button type="submit" className="btn-primary">
                Add Entry
              </button>
            </form>
          </div>
        )}

        {/* Entries List */}
        <div className="entries-section">
          <h3>Your Zakat Entries</h3>
          {entries.length === 0 ? (
            <p className="no-entries">No entries yet. Add your first entry above!</p>
          ) : (
            <div className="entries-list">
              {entries.map((entry) => (
                <div key={entry.id} className="entry-card">
                  <div className="entry-header">
                    <span className="entry-category">{entry.category}</span>
                    <span className="entry-date">
                      {new Date(entry.date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="entry-body">
                    <div className="entry-amount">
                      <span>Amount:</span>
                      <strong>${entry.amount.toFixed(2)}</strong>
                    </div>
                    <div className="entry-zakat">
                      <span>Zakat (2.5%):</span>
                      <strong>${entry.zakat_amount.toFixed(2)}</strong>
                    </div>
                    {entry.description && (
                      <p className="entry-description">{entry.description}</p>
                    )}
                  </div>
                  <div className="entry-actions">
                    <button
                      onClick={() => handleDelete(entry.id)}
                      className="btn-delete"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;