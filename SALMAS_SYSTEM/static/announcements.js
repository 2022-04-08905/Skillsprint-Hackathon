function deleteAnnouncement(id) {
    if (confirm('Are you sure you want to delete this announcement?')) {
        fetch('/delete_announcement', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `id=${id}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error deleting announcement: ' + data.error);
            }
        });
    }
}
