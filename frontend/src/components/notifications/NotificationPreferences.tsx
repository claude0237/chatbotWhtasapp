import React from 'react';
import { useNotificationPreferences } from '../../hooks/useNotifications';

export const NotificationPreferences: React.FC = () => {
  const { preferences, loading, updatePreference } = useNotificationPreferences();

  const handleToggle = async (notificationType: string, enabled: boolean) => {
    await updatePreference({ notification_type: notificationType, enabled });
  };

  const handleChannelChange = async (notificationType: string, channel: string) => {
    const pref = preferences.find(p => p.notification_type === notificationType);
    if (pref) {
      await updatePreference({ notification_type: notificationType, enabled: pref.enabled, channel });
    }
  };

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-500">
        Loading preferences...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Notification Preferences</h3>
      
      <div className="space-y-3">
        {preferences.map((pref) => (
          <div key={pref.id} className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg">
            <div className="flex-1">
              <p className="font-medium text-gray-900">
                {pref.notification_type.replace(/_/g, ' ').toLowerCase()}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {pref.enabled ? 'Enabled' : 'Disabled'}
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <select
                value={pref.channel}
                onChange={(e) => handleChannelChange(pref.notification_type, e.target.value)}
                className="block w-32 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="IN_APP">In App</option>
                <option value="EMAIL">Email</option>
                <option value="SMS">SMS</option>
              </select>
              
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={pref.enabled}
                  onChange={(e) => handleToggle(pref.notification_type, e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
