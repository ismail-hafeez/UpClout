import React, { useState, useEffect } from 'react';
import './styles/globals.css';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import MainPage from './pages/MainPage';
import OwlyIntro from './pages/OwlyIntro';
import OwlyChat from './pages/OwlyChat';
import UserChat from './pages/UserChat';
import ProfilePage from './pages/ProfilePage';
import CampaignDashboard from './pages/CampaignDashboard';
import CampaignDetails from './pages/CampaignDetails';
import { getToken, apiMe, setCurrentUser, clearToken, clearCurrentUser, apiGetConversations } from './services/api';
import { connectSocket, disconnectSocket, getSocket } from './services/socket';

type AppPage = 'landing' | 'login' | 'main' | 'owly-intro' | 'owly-chat' | 'user-chat' | 'campaign-dashboard' | 'campaign-details' | 'profile';

const App: React.FC = () => {
  const [page, setPage] = useState<AppPage>('landing');
  const [currentCampaignId, setCurrentCampaignId] = useState<string | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [totalUnread, setTotalUnread] = useState(0);
  const [targetUsername, setTargetUsername] = useState<string | null>(null);
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    return (localStorage.getItem('theme') as 'dark' | 'light') || 'dark';
  });

  // Apply theme to root element
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const handleToggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

  // Fetch conversations and compute total unread count
  const refreshUnread = async () => {
    try {
      const conversations = await apiGetConversations();
      const total = conversations.reduce((sum: number, c: any) => sum + (c.unread || 0), 0);
      setTotalUnread(total);
    } catch {
      // silently ignore — user may not be logged in yet
    }
  };

  // On mount: check if there's a valid saved token
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setAuthChecked(true);
      return;
    }
    apiMe()
      .then(({ user }) => {
        setCurrentUser(user);
        connectSocket();
        setPage('main');
        refreshUnread();
      })
      .catch(() => {
        clearToken();
        clearCurrentUser();
      })
      .finally(() => setAuthChecked(true));
  }, []);

  // Listen for real-time new messages to update badge
  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    const handleConversationUpdated = () => {
      // Only increment if the user is NOT currently in the chats page
      setPage(currentPage => {
        if (currentPage !== 'user-chat') {
          setTotalUnread(n => n + 1);
        }
        return currentPage;
      });
    };

    socket.on('conversation:updated', handleConversationUpdated);
    return () => {
      socket.off('conversation:updated', handleConversationUpdated);
    };
  }, [page]);

  const handleLogin = () => {
    connectSocket();
    setPage('main');
    refreshUnread();
  };

  const handleLogout = () => {
    disconnectSocket();
    clearToken();
    clearCurrentUser();
    setTotalUnread(0);
    setPage('landing');
  };

  const handleNavigate = (target: string, params?: any) => {
    if (target === 'owly') setPage('owly-intro');
    else if (target === 'chats') {
      setTotalUnread(0); // reset badge when entering chats
      setPage('user-chat');
    }
    else if (target === 'campaigns') setPage('campaign-dashboard');
    else if (target === 'campaign-details') {
      setCurrentCampaignId(params?.campaignId || null);
      setPage('campaign-details');
    }
    else if (target === 'profile') {
      setTargetUsername(params?.username || null);
      setPage('profile');
    }
    else if (target === 'main') setPage('main');
  };

  if (!authChecked) return null; // Avoid flash before token check

  switch (page) {
    case 'landing':
      return <LandingPage onTryNow={() => setPage('login')} />;
    case 'login':
      return <LoginPage onLogin={handleLogin} />;
    case 'owly-intro':
      return <OwlyIntro onContinue={() => setPage('owly-chat')} onBack={() => setPage('main')} />;
    case 'owly-chat':
      return <OwlyChat onBack={() => setPage('owly-intro')} />;
    case 'user-chat':
      return <UserChat onBack={() => setPage('main')} />;
    case 'campaign-dashboard':
      return <CampaignDashboard onNavigate={handleNavigate} onBack={() => setPage('main')} />;
    case 'campaign-details':
      return <CampaignDetails campaignId={currentCampaignId!} onNavigate={handleNavigate} onBack={() => setPage('campaign-dashboard')} />;
    case 'profile':
      return <ProfilePage username={targetUsername!} onBack={() => setPage('main')} />;
    case 'main':
    default:
      return <MainPage onNavigate={handleNavigate as any} onBack={handleLogout} unreadCount={totalUnread} theme={theme} onToggleTheme={handleToggleTheme} />;
  }
};

export default App;