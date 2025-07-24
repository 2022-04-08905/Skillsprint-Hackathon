
        function deleteStudent(id) {
            if (confirm('Are you sure you want to delete this student?')) {
                fetch('/delete_student', {
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
                        alert('Error deleting student: ' + data.error);
                    }
                });
            }
        }
        