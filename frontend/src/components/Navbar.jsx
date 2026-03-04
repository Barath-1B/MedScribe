import { NavLink } from 'react-router-dom';

const links = [
  { to: '/',             label: 'Overview' },
  { to: '/pipeline',     label: 'Pipeline' },
  { to: '/degradation',  label: 'Degradation' },
  { to: '/documents',    label: 'Documents' },
  { to: '/errors',       label: 'Error Breakdown' },
  { to: '/inspector',    label: 'Inspector' },
  { to: '/upload',       label: 'Upload' },
  { to: '/experiment',   label: 'Experiment' },
];

export default function Navbar() {
  return (
    <nav className="navbar">
      <span className="logo">OCR Clinical Analysis</span>
      {links.map(({ to, label }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) => isActive ? 'active' : ''}
        >
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
