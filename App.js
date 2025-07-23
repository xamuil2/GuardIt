import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './firebase';
import LoginScreen from './screens/LoginScreen';
import SignupScreen from './screens/SignupScreen';
import HomeScreen from './screens/HomeScreen';
import MapScreen from './screens/MapScreen';
import IMUScreen from './screens/IMUScreen';
import CameraScreen from './screens/CameraScreen';
import CameraStreamScreen from './screens/CameraStreamScreen';
import NotificationsScreen from './screens/NotificationsScreen';
import ConnectionScreen from './screens/ConnectionScreen';
import ConnectedOptionsScreen from './screens/ConnectedOptionsScreen';

const Stack = createStackNavigator();

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  if (loading) return null;

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }} key={user ? 'authenticated' : 'unauthenticated'}>
        {user ? (
          <>
            <Stack.Screen name="Home" component={HomeScreen} />
            <Stack.Screen name="Map" component={MapScreen} />
            <Stack.Screen name="IMU" component={IMUScreen} />
            <Stack.Screen name="Camera" component={CameraScreen} />
            <Stack.Screen name="CameraStream" component={CameraStreamScreen} />
            <Stack.Screen name="Notifications" component={NotificationsScreen} />
            <Stack.Screen name="Connection" component={ConnectionScreen} />
            <Stack.Screen name="ConnectedOptions" component={ConnectedOptionsScreen} />
          </>
        ) : (
          <>
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="Signup" component={SignupScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
