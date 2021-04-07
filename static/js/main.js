// Register Service Worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker
        .register('./service-worker.js')
        .then(function (registration) {
            console.log('Service Worker Registered');
            return registration;
        })
        .catch(function (err) {
            console.error('Unable to register service worker.', err);
        });
}


// Push Notifications
const pushButton = document.getElementById('push-btn');
pushButton.addEventListener('click', askPermission);
notificationButtonUpdate();

if (!("Notification" in window)) {
    pushButton.hidden;
}

function askPermission(evt) {
    pushButton.disabled = true;
    Notification.requestPermission().then(function (permission) { notificationButtonUpdate(); });

}

function notificationButtonUpdate() {
    if (Notification.permission == 'granted') {
        pushButton.disabled = true;
    } else {
        pushButton.disabled = false;
    }
}
