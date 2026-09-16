/* ============================================================
   Student Confirmation Portal — base JS
   Auto-dismiss alerts after 6 seconds (in addition to Bootstrap dismiss).
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {
    const alerts = document.querySelectorAll(".alert.alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 6000);
    });
});