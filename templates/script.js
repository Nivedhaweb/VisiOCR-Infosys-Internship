document.getElementById('visitor-form').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const name = document.getElementById('name').value;
    const dob = document.getElementById('dob').value;

    // Calculate age based on date of birth
    const today = new Date();
    const birthDate = new Date(dob);
    const age = today.getFullYear() - birthDate.getFullYear();
    const month = today.getMonth() - birthDate.getMonth();
    if (month < 0 || (month === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }

    let eligibility;
    if (age >= 18) {
        eligibility = 'Eligible';
    } else {
        eligibility = 'Not Eligible';
    }

    const passInfo = `Name: ${name}<br>Date of Birth: ${dob}<br>Age: ${age}<br>Eligibility: ${eligibility}`;

    // Display pass information
    document.getElementById('pass-info').innerHTML = passInfo;
});
