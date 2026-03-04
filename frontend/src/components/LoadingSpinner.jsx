export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="loading">
      <div className="spinner" />
      {message}
    </div>
  );
}
