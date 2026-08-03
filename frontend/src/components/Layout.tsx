import { ReactNode } from 'react';
import {
  Header,
  HeaderName,
  HeaderNavigation,
  HeaderMenuItem,
  HeaderGlobalBar,
  HeaderGlobalAction,
  SkipToContent,
} from '@carbon/react';
import {
  Notification,
  UserAvatar,
  Help,
} from '@carbon/icons-react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Layout.scss';

interface LayoutProps {
  children: ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="layout">
      <Header aria-label="Contract AI">
        <SkipToContent />
        <HeaderName href="#" prefix="">
          Contract AI
        </HeaderName>
        <HeaderNavigation aria-label="Contract AI">
          <HeaderMenuItem
            onClick={() => navigate('/dashboard')}
            isActive={isActive('/dashboard')}
          >
            Dashboard
          </HeaderMenuItem>
          <HeaderMenuItem
            onClick={() => navigate('/contracts')}
            isActive={isActive('/contracts')}
          >
            Contracts
          </HeaderMenuItem>
          <HeaderMenuItem
            onClick={() => navigate('/upload')}
            isActive={isActive('/upload')}
          >
            Upload
          </HeaderMenuItem>
        </HeaderNavigation>
        <HeaderGlobalBar>
          <HeaderGlobalAction
            aria-label="Help"
            tooltipAlignment="end"
          >
            <Help size={20} />
          </HeaderGlobalAction>
          <HeaderGlobalAction
            aria-label="Notifications"
            tooltipAlignment="end"
          >
            <Notification size={20} />
          </HeaderGlobalAction>
          <HeaderGlobalAction
            aria-label="User Avatar"
            tooltipAlignment="end"
          >
            <UserAvatar size={20} />
          </HeaderGlobalAction>
        </HeaderGlobalBar>
      </Header>
      <main className="main-content">{children}</main>
    </div>
  );
};

export default Layout;

// Made with Bob
