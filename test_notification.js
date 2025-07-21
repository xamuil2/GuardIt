import NotificationService from './services/NotificationService';

async function testNotification() {

  try {
    const initialized = await NotificationService.initialize();

    if (!initialized) {

      return;
    }

    const result = await NotificationService.triggerSuspiciousActivityAlert();

    if (result) {

    } else {

    }
    
  } catch (error) {

  }
}

export { testNotification };

if (typeof window !== 'undefined') {
  testNotification();
}
