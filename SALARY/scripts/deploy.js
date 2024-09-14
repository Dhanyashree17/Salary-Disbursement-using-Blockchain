async function main() {
    const [deployer] = await ethers.getSigners();

    console.log("Deploying contracts with the account:", deployer.address);

    const balance = await deployer.getBalance();
    console.log("Account balance:", balance.toString());

    const SalaryDisbursement = await ethers.getContractFactory("SalaryDisbursement");
    const salaryDisbursement = await SalaryDisbursement.deploy();

    console.log("SalaryDisbursement contract address:", salaryDisbursement.address);
}

main()
    .then(() => process.exit(0))
    .catch(error => {
        console.error(error);
        process.exit(1);
    });
